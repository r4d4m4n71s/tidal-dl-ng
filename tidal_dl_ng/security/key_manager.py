"""
Secure key management for API keys and secrets.

This module provides secure storage and retrieval of API keys using
machine-specific encryption and environment variable support.
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("Warning: cryptography package not installed. Using fallback encryption.")


class SecureKeyManager:
    """Manages secure storage and retrieval of API keys."""
    
    def __init__(self):
        """Initialize the secure key manager."""
        self.config_path = Path.home() / ".tidal-dl-ng" / "secure_config"
        self.config_path.mkdir(parents=True, exist_ok=True)
        self._key_index = 0
        self._cached_keys: Optional[List[Dict[str, Any]]] = None
        
    def _get_machine_id(self) -> str:
        """Generate a machine-specific identifier."""
        # Combine various machine-specific data
        machine_parts = [
            os.environ.get('COMPUTERNAME', ''),
            os.environ.get('USER', ''),
            os.environ.get('USERNAME', ''),
            os.environ.get('HOSTNAME', ''),
            # Add more machine-specific data if available
            str(os.getuid()) if hasattr(os, 'getuid') else '',
        ]
        return ''.join(filter(None, machine_parts))
        
    def _get_or_create_key(self) -> bytes:
        """Generate or retrieve encryption key for config."""
        key_file = self.config_path / ".key"
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception:
                # If key file is corrupted, regenerate
                pass
                
        if CRYPTOGRAPHY_AVAILABLE:
            # Use machine-specific data for key derivation
            machine_id = self._get_machine_id()
            if not machine_id:
                machine_id = "default-tidal-dl-ng"
                
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'tidal-dl-ng-salt-v1',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        else:
            # Fallback: simple key generation (less secure)
            import hashlib
            machine_id = self._get_machine_id() or "default"
            key_data = hashlib.sha256(f"tidal-dl-ng-{machine_id}".encode()).digest()
            key = base64.urlsafe_b64encode(key_data)
            
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions on Unix-like systems
            if hasattr(os, 'chmod'):
                os.chmod(key_file, 0o600)
        except Exception as e:
            print(f"Warning: Could not save encryption key: {e}")
            
        return key
    
    def encrypt_keys(self, api_keys: List[Dict[str, Any]]) -> bytes:
        """Encrypt API keys for storage."""
        if CRYPTOGRAPHY_AVAILABLE:
            f = Fernet(self._get_or_create_key())
            encrypted = f.encrypt(json.dumps(api_keys).encode())
        else:
            # Fallback: base64 encoding (not secure, but better than plain text)
            import warnings
            warnings.warn("Using base64 encoding instead of encryption. Install 'cryptography' for better security.")
            encrypted = base64.b64encode(json.dumps(api_keys).encode())
            
        return encrypted
    
    def decrypt_keys(self) -> Optional[List[Dict[str, Any]]]:
        """Decrypt stored API keys."""
        # Check cache first
        if self._cached_keys is not None:
            return self._cached_keys
            
        keys_file = self.config_path / "api_keys.enc"
        
        if not keys_file.exists():
            return None
            
        try:
            with open(keys_file, 'rb') as file:
                encrypted_data = file.read()
                
            if CRYPTOGRAPHY_AVAILABLE:
                f = Fernet(self._get_or_create_key())
                decrypted = f.decrypt(encrypted_data)
            else:
                # Fallback: base64 decoding
                decrypted = base64.b64decode(encrypted_data)
                
            self._cached_keys = json.loads(decrypted.decode())
            return self._cached_keys
            
        except Exception as e:
            print(f"Error decrypting keys: {e}")
            return None
    
    def save_keys(self, api_keys: List[Dict[str, Any]]) -> bool:
        """Save encrypted API keys to storage."""
        try:
            encrypted = self.encrypt_keys(api_keys)
            keys_file = self.config_path / "api_keys.enc"
            
            with open(keys_file, 'wb') as f:
                f.write(encrypted)
                
            # Set restrictive permissions
            if hasattr(os, 'chmod'):
                os.chmod(keys_file, 0o600)
                
            # Clear cache to force reload
            self._cached_keys = None
            return True
            
        except Exception as e:
            print(f"Error saving keys: {e}")
            return False
    
    def rotate_keys(self, keys_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rotate through available keys to distribute usage."""
        if not keys_list:
            raise ValueError("No keys available for rotation")
            
        key = keys_list[self._key_index % len(keys_list)]
        self._key_index += 1
        
        return key
    
    def get_key_from_env(self) -> Optional[Dict[str, Any]]:
        """Get API key from environment variables."""
        client_id = os.environ.get('TIDAL_CLIENT_ID')
        client_secret = os.environ.get('TIDAL_CLIENT_SECRET')
        
        if client_id and client_secret:
            return {
                "clientId": client_id,
                "clientSecret": client_secret,
                "platform": "Environment",
                "formats": "All",
                "valid": "True"
            }
        return None
    
    def migrate_legacy_keys(self, legacy_keys: List[Dict[str, Any]]) -> bool:
        """Migrate legacy hardcoded keys to secure storage."""
        try:
            # Check if migration already done
            existing_keys = self.decrypt_keys()
            if existing_keys:
                print("Keys already migrated to secure storage.")
                return True
                
            # Save legacy keys securely
            return self.save_keys(legacy_keys)
            
        except Exception as e:
            print(f"Error during key migration: {e}")
            return False
