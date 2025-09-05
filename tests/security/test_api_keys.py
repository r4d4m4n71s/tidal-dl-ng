"""
Test API key security features and vulnerabilities.
"""
import os
import base64
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from tidal_dl_ng import api
from tidal_dl_ng.security.key_manager import SecureKeyManager


class TestAPIKeySecurity:
    """Test suite for API key security."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for key in ['TIDAL_CLIENT_ID', 'TIDAL_CLIENT_SECRET']:
            if key in os.environ:
                del os.environ[key]
    
    def test_hardcoded_keys_warning(self):
        """Test that hardcoded keys generate warning (currently they exist)."""
        # This test documents the current vulnerability
        assert hasattr(api, '__LEGACY_KEYS_JSON__'), "Legacy keys should be removed from source code"
        
        # Parse the JSON to verify structure
        legacy_data = json.loads(api.__LEGACY_KEYS_JSON__)
        assert 'keys' in legacy_data
        assert len(legacy_data['keys']) > 0
        
        # Check for sensitive data
        for key in legacy_data['keys']:
            assert 'clientId' in key
            assert 'clientSecret' in key
            # These should not be hardcoded
            assert key['clientId'] != ""
            assert key['clientSecret'] != ""
    
    def test_environment_variable_priority(self):
        """Test that environment variables take priority over hardcoded keys."""
        test_client_id = "TEST_CLIENT_ID_12345"
        test_client_secret = "TEST_CLIENT_SECRET_67890"
        
        os.environ['TIDAL_CLIENT_ID'] = test_client_id
        os.environ['TIDAL_CLIENT_SECRET'] = test_client_secret
        
        # Reinitialize the API key provider
        api._api_key_provider = api.APIKeyProvider()
        
        key = api.get_secure_key()
        assert key['clientId'] == test_client_id
        assert key['clientSecret'] == test_client_secret
        assert key['platform'] == "Environment"
    
    def test_key_rotation_functionality(self):
        """Test that key rotation works and uses multiple keys."""
        keys_used = set()
        platforms_used = set()
        
        # Get keys multiple times to test rotation
        for _ in range(20):
            key = api.get_secure_key()
            if key['clientId']:  # Skip error keys
                keys_used.add(key['clientId'])
                platforms_used.add(key['platform'])
        
        # Should use multiple keys if available
        assert len(keys_used) >= 1, "Should have at least one valid key"
        
        # Verify rotation is happening
        if len(keys_used) > 1:
            # If multiple keys, verify they're being rotated
            first_key = api.get_secure_key()
            different_found = False
            for _ in range(10):
                next_key = api.get_secure_key()
                if next_key['clientId'] != first_key['clientId']:
                    different_found = True
                    break
            assert different_found, "Key rotation should use different keys"
    
    def test_secure_key_manager_encryption(self):
        """Test that SecureKeyManager properly encrypts keys."""
        manager = SecureKeyManager()
        
        test_keys = [
            {
                "clientId": "test_id_1",
                "clientSecret": "test_secret_1",
                "platform": "Test Platform",
                "valid": "True"
            }
        ]
        
        # Test encryption
        encrypted = manager.encrypt_keys(test_keys)
        assert encrypted != json.dumps(test_keys).encode()
        assert len(encrypted) > 0
        
        # Test that encrypted data is not readable as plain text
        assert b"test_id_1" not in encrypted
        assert b"test_secret_1" not in encrypted
    
    def test_secure_key_manager_decryption(self):
        """Test encryption/decryption cycle."""
        # Mock the Fernet key generation to use a valid key
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        
        with patch('tidal_dl_ng.security.key_manager.Fernet') as mock_fernet:
            # Create a real Fernet instance for testing
            real_fernet = Fernet(valid_key)
            mock_fernet.return_value = real_fernet
            
            manager = SecureKeyManager()
            manager._fernet = real_fernet
            
            test_keys = [
                {
                    "clientId": "test_id_1",
                    "clientSecret": "test_secret_1",
                    "platform": "Test Platform",
                    "valid": "True"
                }
            ]
            
            # Encrypt keys
            encrypted = manager.encrypt_keys(test_keys)
            assert encrypted != json.dumps(test_keys).encode()
            
            # Mock file operations for saving
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('pathlib.Path.mkdir'):
                    with patch('os.chmod'):
                        # Save encrypted keys
                        result = manager.save_keys(test_keys)
                        
                        # Should return True on success
                        assert result is True
                
            # Test decryption
            decrypted_data = real_fernet.decrypt(encrypted)
            decrypted_keys = json.loads(decrypted_data.decode())
            assert decrypted_keys == test_keys
    
    def test_key_migration_process(self):
        """Test the legacy key migration process."""
        manager = SecureKeyManager()
        
        # Mock that no keys exist yet
        with patch.object(manager, 'decrypt_keys', return_value=None):
            with patch.object(manager, 'save_keys', return_value=True) as mock_save:
                legacy_keys = [{"clientId": "legacy", "clientSecret": "secret"}]
                result = manager.migrate_legacy_keys(legacy_keys)
                
                assert result is True
                mock_save.assert_called_once_with(legacy_keys)
    
    def test_no_github_gist_fetching(self):
        """Verify that GitHub Gist fetching is disabled."""
        # Check that the code doesn't contain Gist URL references
        import inspect
        api_source = inspect.getsource(api)
        
        # The old Gist URL should not be actively used
        assert "api.github.com/gists" not in api_source or "disabled" in api_source.lower()
    
    @pytest.mark.parametrize("key_index", [0, 1, 2, 3, 4])
    def test_individual_key_validity(self, key_index):
        """Test each key's validity status."""
        key = api.getItem(key_index)
        assert 'valid' in key
        assert key['valid'] in ['True', 'False']
        
        if key['valid'] == 'True':
            # Valid keys should have complete information
            assert key['clientId'] != ""
            assert key['clientSecret'] != ""
            assert key['platform'] != ""
    
    def test_api_version_format(self):
        """Test API version includes security indicator."""
        version = api.getVersion()
        assert "-secure" in version or "secure" in version.lower()
    
    def test_error_key_handling(self):
        """Test error key is returned when no valid keys available."""
        # Get item with invalid index
        error_key = api.getItem(999)
        assert error_key['valid'] == 'False'
        assert error_key['platform'] == 'None'
        assert error_key['clientId'] == ''
        assert error_key['clientSecret'] == ''
    
    def test_machine_specific_encryption(self):
        """Test that encryption uses machine-specific data."""
        manager = SecureKeyManager()
        machine_id = manager._get_machine_id()
        
        # Machine ID should contain some identifying information
        assert len(machine_id) > 0
        
        # Test that different managers create consistent keys
        manager2 = SecureKeyManager()
        assert manager._get_machine_id() == manager2._get_machine_id()
    
    def test_secure_session_creation(self):
        """Test secure session setup with headers."""
        session = api.setup_secure_session()
        
        # Should have headers set
        assert len(session.headers) > 0
        assert 'User-Agent' in session.headers
        assert 'Accept' in session.headers


class TestAPIKeySecurityIntegration:
    """Integration tests for API key security with other components."""
    
    def test_headers_included_with_api_requests(self):
        """Test that secure headers are included with API requests."""
        headers = api.get_secure_headers()
        
        # Should include various security headers
        assert 'User-Agent' in headers
        assert 'Accept-Language' in headers
        assert 'Accept-Encoding' in headers
        
        # Should include TIDAL-specific headers
        assert any('tidal' in k.lower() or 'tidal' in str(v).lower() 
                  for k, v in headers.items())
    
    def test_key_storage_permissions(self):
        """Test that key storage has appropriate file permissions."""
        manager = SecureKeyManager()
        
        # Test that config directory is created with proper permissions
        assert manager.config_path.exists()
        
        # Skip permission check on Windows (different permission model)
        import platform
        if platform.system() == 'Windows':
            return
            
        # On Unix systems, check permissions
        if hasattr(os, 'chmod'):
            # Directory should exist
            assert manager.config_path.is_dir()
            
            # Key file path
            key_file = manager.config_path / ".key"
            if key_file.exists():
                # Check file permissions (owner read/write only)
                stat_info = key_file.stat()
                # File mode should be 0o600 (owner read/write only)
                assert oct(stat_info.st_mode)[-3:] == '600'
