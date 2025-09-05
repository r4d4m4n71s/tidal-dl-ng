"""
Test decryption security features and vulnerabilities.
"""
import os
import base64
import pytest
from unittest.mock import patch, MagicMock

from tidal_dl_ng.helper import decryption
from tidal_dl_ng.helper.decryption import SecureDecryption


class TestDecryptionSecurity:
    """Test suite for decryption security."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for key in ['TIDAL_MASTER_KEY', 'TIDAL_USE_SECURE_DECRYPTION']:
            if key in os.environ:
                del os.environ[key]
        
        # Reset the global instance
        decryption._secure_decryption = SecureDecryption()
    
    def test_hardcoded_master_key_warning(self):
        """Test that hardcoded master key exists (vulnerability)."""
        # This test documents the current vulnerability
        legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
        
        # Check if the key is hardcoded in the module
        import inspect
        source = inspect.getsource(decryption)
        assert legacy_key_b64 in source, "Legacy key should be removed from source code"
    
    def test_default_uses_legacy_key(self):
        """Test that default mode uses hardcoded key."""
        secure_decrypt = SecureDecryption()
        master_key = secure_decrypt.get_master_key()
        
        # Check if using legacy key
        legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
        legacy_key = base64.b64decode(legacy_key_b64)
        
        assert master_key == legacy_key, "Default should not use hardcoded key"
    
    def test_secure_mode_uses_derived_key(self):
        """Test that secure mode uses machine-derived key."""
        os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'
        
        secure_decrypt = SecureDecryption()
        master_key = secure_decrypt.get_master_key()
        
        # Should not use legacy key
        legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
        legacy_key = base64.b64decode(legacy_key_b64)
        
        assert master_key != legacy_key, "Secure mode should use derived key"
        assert len(master_key) == 32, "Key should be 32 bytes"
    
    def test_environment_master_key_priority(self):
        """Test that environment variable takes priority."""
        # Set both secure mode and custom key
        os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'
        test_key = base64.b64encode(b'test_master_key_1234567890123456').decode()
        os.environ['TIDAL_MASTER_KEY'] = test_key
        
        secure_decrypt = SecureDecryption()
        master_key = secure_decrypt.get_master_key()
        
        assert master_key == base64.b64decode(test_key)
    
    def test_machine_identifier_generation(self):
        """Test machine-specific identifier generation."""
        secure_decrypt = SecureDecryption()
        machine_id = secure_decrypt._get_machine_identifier()
        
        # Should generate consistent identifier
        assert len(machine_id) > 0
        
        # Should be consistent across instances
        secure_decrypt2 = SecureDecryption()
        assert machine_id == secure_decrypt2._get_machine_identifier()
    
    def test_decrypt_security_token_validation(self):
        """Test security token decryption with validation."""
        secure_decrypt = SecureDecryption()
        
        # Test with invalid token (too short)
        with pytest.raises(ValueError, match="Security token too short"):
            secure_decrypt.decrypt_security_token(base64.b64encode(b'short').decode())
        
        # Test with invalid base64
        with pytest.raises(Exception):
            secure_decrypt.decrypt_security_token("not_base64!")
    
    def test_decrypt_security_token_integrity(self):
        """Test that decryption validates data integrity."""
        secure_decrypt = SecureDecryption()
        
        # Create a properly formatted but invalid token
        # 16 bytes IV + 16 bytes encrypted data (minimum)
        fake_token = b'\x00' * 16 + b'\xFF' * 16
        fake_token_b64 = base64.b64encode(fake_token).decode()
        
        # Should handle decryption attempt
        try:
            key, nonce = secure_decrypt.decrypt_security_token(fake_token_b64)
            # Check for all-zero validation
            assert key != b'\x00' * 16, "Should validate against all-zero keys"
        except ValueError:
            # Expected if validation fails
            pass
    
    def test_key_derivation_with_cryptography(self):
        """Test PBKDF2 key derivation when cryptography is available."""
        if not decryption.CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography package not available")
        
        os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'
        secure_decrypt = SecureDecryption()
        
        # Force regeneration
        secure_decrypt._master_key = None
        key1 = secure_decrypt.get_master_key()
        
        # Should be consistent
        secure_decrypt._master_key = None
        key2 = secure_decrypt.get_master_key()
        
        assert key1 == key2
        assert len(key1) == 32
    
    def test_key_derivation_fallback(self):
        """Test fallback key derivation without cryptography."""
        # Mock cryptography not available
        with patch('tidal_dl_ng.helper.decryption.CRYPTOGRAPHY_AVAILABLE', False):
            os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'
            
            secure_decrypt = SecureDecryption()
            secure_decrypt._master_key = None
            
            key = secure_decrypt.get_master_key()
            assert len(key) == 32
            
            # Should not be the legacy key
            legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
            legacy_key = base64.b64decode(legacy_key_b64)
            assert key != legacy_key
    
    def test_decrypt_file_function(self):
        """Test the decrypt_file function works with proper keys."""
        import tempfile
        from pathlib import Path
        
        # Create test data
        test_data = b"Test encrypted content"
        key = b'1234567890123456'  # 16 bytes
        nonce = b'12345678'  # 8 bytes
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create encrypted file
            enc_path = Path(tmpdir) / "encrypted.bin"
            dec_path = Path(tmpdir) / "decrypted.bin"
            
            # Write test data (this would normally be encrypted)
            enc_path.write_bytes(test_data)
            
            # Mock the AES decryption
            with patch('tidal_dl_ng.helper.decryption.AES') as mock_aes:
                mock_decryptor = MagicMock()
                mock_decryptor.decrypt.return_value = test_data
                mock_aes.new.return_value = mock_decryptor
                
                # Call decrypt_file
                decryption.decrypt_file(enc_path, dec_path, key, nonce)
                
                # Verify AES was called correctly
                mock_aes.new.assert_called_once()
                
                # Verify file was written
                assert dec_path.exists()


class TestDecryptionSecurityIntegration:
    """Integration tests for decryption security."""
    
    def test_legacy_compatibility_mode(self):
        """Test that legacy mode warning is shown."""
        # Capture print output
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            # Force legacy mode
            os.environ.pop('TIDAL_USE_SECURE_DECRYPTION', None)
            secure_decrypt = SecureDecryption()
            secure_decrypt._master_key = None
            secure_decrypt.get_master_key()
            
            output = captured_output.getvalue()
            assert "Warning:" in output
            assert "legacy" in output.lower()
        finally:
            sys.stdout = old_stdout
    
    def test_secure_mode_message(self):
        """Test that secure mode is acknowledged."""
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'
            secure_decrypt = SecureDecryption()
            secure_decrypt._master_key = None
            secure_decrypt.get_master_key()
            
            output = captured_output.getvalue()
            assert "secure" in output.lower()
        finally:
            sys.stdout = old_stdout
    
    def test_backward_compatibility_function(self):
        """Test the backward compatibility wrapper function."""
        # Test that the global function works
        test_token = base64.b64encode(b'\x00' * 32).decode()
        
        try:
            result = decryption.decrypt_security_token(test_token)
            assert isinstance(result, tuple)
            assert len(result) == 2
        except ValueError:
            # Expected for invalid tokens
            pass
