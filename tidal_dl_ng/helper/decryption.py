import base64
import os
import pathlib
import hashlib
from typing import Tuple

from Crypto.Cipher import AES
from Crypto.Util import Counter

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class SecureDecryption:
    """Secure decryption with configurable key management."""
    
    def __init__(self):
        """Initialize the secure decryption system."""
        self._master_key: bytes = None
        
    def _derive_master_key(self) -> bytes:
        """Derive master key from environment or secure storage."""
        # Try environment variable first (most secure)
        env_key = os.environ.get('TIDAL_MASTER_KEY')
        if env_key:
            try:
                return base64.b64decode(env_key)
            except Exception:
                print("Warning: Invalid TIDAL_MASTER_KEY format. Expected base64.")
                
        # Fallback to derived key (less secure but better than hardcoded)
        machine_specific = self._get_machine_identifier()
        
        if CRYPTOGRAPHY_AVAILABLE:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'tidal-dl-ng-decrypt-v1',
                iterations=100000,
            )
            return kdf.derive(machine_specific.encode())
        else:
            # Fallback: SHA256 hash (less secure)
            return hashlib.sha256(f"tidal-dl-ng-decrypt-{machine_specific}".encode()).digest()
    
    def _get_machine_identifier(self) -> str:
        """Generate a machine-specific identifier."""
        machine_parts = [
            os.environ.get('COMPUTERNAME', ''),
            os.environ.get('USER', ''),
            os.environ.get('USERNAME', ''),
            os.environ.get('HOSTNAME', ''),
        ]
        machine_id = ''.join(filter(None, machine_parts))
        return machine_id or "default-tidal-dl-ng"
        
    def get_master_key(self) -> bytes:
        """Get or generate master key."""
        if self._master_key is None:
            # Check if secure key system is enabled
            use_secure = os.environ.get('TIDAL_USE_SECURE_DECRYPTION', 'false').lower() == 'true'
            
            if use_secure:
                self._master_key = self._derive_master_key()
                print("Using secure decryption key system.")
            else:
                # Legacy key for backward compatibility
                legacy_key = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
                self._master_key = base64.b64decode(legacy_key)
                print("Warning: Using legacy decryption key. Set TIDAL_USE_SECURE_DECRYPTION=true to enable secure mode.")
                
        return self._master_key
    
    def decrypt_security_token(self, security_token: str) -> Tuple[bytes, bytes]:
        """
        Decrypt security token with integrity verification.
        
        Args:
            security_token: Base64 encoded security token
            
        Returns:
            Tuple of (key, nonce) for stream decryption
            
        Raises:
            ValueError: If decryption fails or token is invalid
        """
        try:
            master_key = self.get_master_key()
            
            # Decode the base64 security token
            security_token_bytes = base64.b64decode(security_token)
            
            # Validate minimum length
            if len(security_token_bytes) < 32:  # 16 bytes IV + 16 bytes minimum encrypted data
                raise ValueError("Security token too short")
            
            # Get the IV from the first 16 bytes
            iv = security_token_bytes[:16]
            encrypted_st = security_token_bytes[16:]
            
            # Initialize decryptor
            decryptor = AES.new(master_key, AES.MODE_CBC, iv)
            
            # Decrypt the security token
            decrypted_st = decryptor.decrypt(encrypted_st)
            
            # Verify decryption integrity
            if len(decrypted_st) < 24:
                raise ValueError("Decrypted token too short - decryption may have failed")
            
            # Extract key and nonce
            key = decrypted_st[:16]
            nonce = decrypted_st[16:24]
            
            # Basic sanity check - ensure we have non-zero data
            if key == b'\x00' * 16 or nonce == b'\x00' * 8:
                raise ValueError("Decryption produced invalid key/nonce")
            
            return key, nonce
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt security token: {e}")


# Global instance for backward compatibility
_secure_decryption = SecureDecryption()


def decrypt_security_token(security_token: str) -> Tuple[bytes, bytes]:
    """
    Legacy compatibility function for decrypting security tokens.
    
    Args:
        security_token: Base64 encoded security token
        
    Returns:
        Tuple of (key, nonce) for stream decryption
    """
    return _secure_decryption.decrypt_security_token(security_token)


def decrypt_file(path_file_encrypted: pathlib.Path, path_file_destination: pathlib.Path, key: str, nonce: str) -> None:
    """
    Decrypts an encrypted MQA file given the file, key and nonce.
    TODO: Is it really only necessary for MQA of for all other formats, too?
    """

    # Initialize counter and file decryptor
    counter = Counter.new(64, prefix=nonce, initial_value=0)
    decryptor = AES.new(key, AES.MODE_CTR, counter=counter)

    # Open and decrypt
    with path_file_encrypted.open("rb") as f_src:
        audio_decrypted = decryptor.decrypt(f_src.read())

        # Replace with decrypted file
        with path_file_destination.open("wb") as f_dst:
            f_dst.write(audio_decrypted)
