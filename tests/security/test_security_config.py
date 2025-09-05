"""
Test security configuration and integration.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from tidal_dl_ng.config import Settings
from tidal_dl_ng.model.cfg import Settings as ModelSettings


class TestSecurityConfiguration:
    """Test suite for security-related configuration."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear environment variables
        env_vars = [
            'TIDAL_CLIENT_ID', 
            'TIDAL_CLIENT_SECRET',
            'TIDAL_MASTER_KEY',
            'TIDAL_USE_SECURE_DECRYPTION'
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_proxy_configuration(self):
        """Test proxy configuration settings."""
        settings = Settings()
        
        # Check default proxy settings
        assert hasattr(settings.data, 'proxy_enabled')
        assert hasattr(settings.data, 'proxy_host')
        assert hasattr(settings.data, 'proxy_port')
        assert hasattr(settings.data, 'proxy_type')
        assert hasattr(settings.data, 'proxy_use_auth')
        assert hasattr(settings.data, 'proxy_username')
        assert hasattr(settings.data, 'proxy_password')
        
        # Default should be disabled
        assert settings.data.proxy_enabled is False
        assert settings.data.proxy_type == 'HTTP'
    
    def test_download_delay_configuration(self):
        """Test download delay configuration."""
        settings = Settings()
        
        # Check delay settings exist
        assert hasattr(settings.data, 'download_delay')
        assert hasattr(settings.data, 'download_delay_sec_min')
        assert hasattr(settings.data, 'download_delay_sec_max')
        
        # Check reasonable defaults
        assert isinstance(settings.data.download_delay, bool)
        assert settings.data.download_delay_sec_min >= 0
        assert settings.data.download_delay_sec_max > settings.data.download_delay_sec_min
    
    def test_security_environment_variables(self):
        """Test that environment variables are checked."""
        # Set test environment variables
        os.environ['TIDAL_CLIENT_ID'] = 'test_client_id'
        os.environ['TIDAL_CLIENT_SECRET'] = 'test_client_secret'
        os.environ['TIDAL_MASTER_KEY'] = 'dGVzdF9tYXN0ZXJfa2V5XzEyMzQ1Njc4OTAxMjM0NTY='  # base64
        os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'
        
        # Import modules that check environment
        from tidal_dl_ng import api
        from tidal_dl_ng.helper import decryption
        
        # API should use environment keys
        key = api.get_secure_key()
        assert key['platform'] == 'Environment'
        
        # Decryption should use secure mode
        secure_decrypt = decryption.SecureDecryption()
        secure_decrypt._master_key = None
        master_key = secure_decrypt.get_master_key()
        
        # Should use the environment key
        import base64
        expected_key = base64.b64decode(os.environ['TIDAL_MASTER_KEY'])
        assert master_key == expected_key
    
    def test_concurrent_download_settings(self):
        """Test concurrent download configuration."""
        settings = Settings()
        
        # Check settings exist
        assert hasattr(settings.data, 'downloads_concurrent_max')
        assert hasattr(settings.data, 'downloads_simultaneous_per_track_max')
        
        # Should have reasonable defaults
        assert settings.data.downloads_concurrent_max > 0
        assert settings.data.downloads_simultaneous_per_track_max > 0
        assert settings.data.downloads_concurrent_max <= 50  # Not too high
    
    def test_metadata_security_settings(self):
        """Test metadata-related security settings."""
        settings = Settings()
        
        # Check metadata settings that affect fingerprinting
        assert hasattr(settings.data, 'metadata_cover_embed')
        assert hasattr(settings.data, 'metadata_cover_dimension')
        assert hasattr(settings.data, 'metadata_replay_gain')
        
        # Check file naming settings that affect patterns
        assert hasattr(settings.data, 'format_album')
        assert hasattr(settings.data, 'format_track')
        assert hasattr(settings.data, 'format_playlist')
    
    def test_security_defaults_are_safe(self):
        """Test that default security settings are safe."""
        settings = Settings()
        
        # Proxy should be disabled by default
        assert settings.data.proxy_enabled is False
        
        # Download delays should be reasonable
        if settings.data.download_delay:
            assert settings.data.download_delay_sec_min >= 1.0
            assert settings.data.download_delay_sec_max >= 3.0
    
    def test_path_security(self):
        """Test path-related security settings."""
        settings = Settings()
        
        # Check path settings
        assert hasattr(settings.data, 'download_base_path')
        
        # Path should not contain sensitive info
        base_path = settings.data.download_base_path
        assert 'password' not in base_path.lower()
        assert 'secret' not in base_path.lower()
    
    @pytest.mark.parametrize("proxy_type", ["HTTP", "HTTPS", "SOCKS5"])
    def test_proxy_type_validation(self, proxy_type):
        """Test different proxy types."""
        settings = Settings()
        
        # Should accept standard proxy types
        settings.data.proxy_type = proxy_type
        assert settings.data.proxy_type == proxy_type


class TestSecurityIntegrationWithDownload:
    """Test security integration with download module."""
    
    def test_download_initializes_security_modules(self):
        """Test that Download class initializes security modules."""
        from tidal_dl_ng.download import Download
        
        # Check that Download has security attributes
        mock_session = MagicMock()
        mock_logger = MagicMock()
        
        with patch('tidal_dl_ng.download.Settings'):
            download = Download(
                session=mock_session,
                path_base="/test/path",
                fn_logger=mock_logger
            )
            
            # Should have security components
            assert hasattr(download, 'request_obfuscator')
            assert hasattr(download, 'header_manager')
            assert hasattr(download, 'metadata_obfuscator')
    
    def test_download_uses_request_obfuscator(self):
        """Test that download uses request obfuscator for delays."""
        from tidal_dl_ng.download import Download
        
        # Check that _perform_post_processing uses obfuscator
        assert hasattr(Download, '_perform_post_processing')
        
        # Method should reference request_obfuscator
        import inspect
        source = inspect.getsource(Download._perform_post_processing)
        assert 'request_obfuscator' in source
        assert 'get_dynamic_delay' in source
    
    def test_security_modules_are_imported(self):
        """Test that security modules are properly imported."""
        # These imports should work
        from tidal_dl_ng.security import key_manager
        from tidal_dl_ng.security import header_manager
        from tidal_dl_ng.security import request_obfuscator
        from tidal_dl_ng.security import metadata_obfuscator
        
        # Should have the main classes
        assert hasattr(key_manager, 'SecureKeyManager')
        assert hasattr(header_manager, 'HeaderManager')
        assert hasattr(request_obfuscator, 'RequestObfuscator')
        assert hasattr(metadata_obfuscator, 'MetadataObfuscator')


class TestSecurityVulnerabilityTracking:
    """Tests that track known security vulnerabilities."""
    
    def test_hardcoded_api_keys_vulnerability(self):
        """Track that hardcoded API keys still exist."""
        from tidal_dl_ng import api
        
        # This test will fail when the vulnerability is fixed
        assert hasattr(api, '__LEGACY_KEYS_JSON__'), "FIXED: Hardcoded keys removed!"
        
        # Document the vulnerability
        legacy_json = api.__LEGACY_KEYS_JSON__
        assert 'OmDtrzFgyVVL6uW56OnFA2COiabqm' in legacy_json  # Fire TV client ID
        assert 'zU4XHVVkc2tDPo4t' in legacy_json  # Android Auto client ID
    
    def test_hardcoded_decryption_key_vulnerability(self):
        """Track that hardcoded decryption key still exists."""
        from tidal_dl_ng.helper import decryption
        
        # This test will fail when the vulnerability is fixed
        import inspect
        source = inspect.getsource(decryption)
        
        legacy_key = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
        assert legacy_key in source, "FIXED: Hardcoded decryption key removed!"
    
    def test_metadata_obfuscation_not_integrated(self):
        """Track that metadata obfuscation is not integrated."""
        from tidal_dl_ng.download import Download
        
        # Check metadata_write method
        import inspect
        source = inspect.getsource(Download.metadata_write)
        
        # Should not use metadata_obfuscator yet
        assert 'metadata_obfuscator' not in source, "FIXED: Metadata obfuscation integrated!"
        assert 'create_metadata_fingerprint_resistance' not in source
    
    def test_default_security_mode_is_legacy(self):
        """Track that secure mode is not default."""
        # Clear environment
        if 'TIDAL_USE_SECURE_DECRYPTION' in os.environ:
            del os.environ['TIDAL_USE_SECURE_DECRYPTION']
        
        from tidal_dl_ng.helper.decryption import SecureDecryption
        
        # Create new instance
        secure_decrypt = SecureDecryption()
        master_key = secure_decrypt.get_master_key()
        
        # Check if using legacy key
        import base64
        legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
        legacy_key = base64.b64decode(legacy_key_b64)
        
        assert master_key == legacy_key, "FIXED: Secure mode is now default!"
    
    def test_proxy_not_used_in_downloads(self):
        """Track that proxy configuration is not used in actual downloads."""
        from tidal_dl_ng.download import Download
        
        # Check _download_segment method
        import inspect
        source = inspect.getsource(Download._download_segment)
        
        # Should not reference proxy settings
        assert 'proxy' not in source.lower() or 'proxy_enabled' not in source, "FIXED: Proxy support integrated!"
