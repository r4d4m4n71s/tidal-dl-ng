"""Network integration tests for TIDAL-DL-NG components.

This module tests the integration between NetworkManager and various application components
including Downloads, RequestsClient, and fallback mechanisms.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from tidal_dl_ng.network import NetworkManager
from tidal_dl_ng.download import Download, RequestsClient
from tidal_dl_ng.config import Settings, Tidal
from tests.network.unit.conftest import MockResponse, TEST_GIST_RESPONSE


class TestDownloadIntegration:
    """Test Download class integration with NetworkManager."""
    
    def test_download_class_network_manager_usage(self, mock_tidal_session, temp_directory, mock_logger):
        """Test that Download class uses NetworkManager."""
        download = Download(
            session=mock_tidal_session,
            path_base=str(temp_directory),
            fn_logger=mock_logger
        )
        
        # Verify NetworkManager is initialized
        assert hasattr(download, 'network_manager')
        assert isinstance(download.network_manager, NetworkManager)
    
    def test_requests_client_network_manager_usage(self):
        """Test that RequestsClient uses NetworkManager."""
        client = RequestsClient()
        
        # Verify NetworkManager is initialized
        assert hasattr(client, 'network_manager')
        assert isinstance(client.network_manager, NetworkManager)
    
    def test_requests_client_download_with_network_manager(self):
        """Test RequestsClient download method uses NetworkManager."""
        with patch('tidal_dl_ng.download.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_response = MockResponse(success=True, content="test content")
            mock_nm.make_request.return_value = mock_response
            mock_nm_class.return_value = mock_nm
            
            client = RequestsClient()
            content, url = client.download("https://example.com/test")
            
            # Verify NetworkManager was used
            mock_nm.make_request.assert_called_once()
            assert content == "test content"
            assert url == "https://example.com/test"
    
    def test_requests_client_fallback_mechanism(self):
        """Test RequestsClient fallback to direct requests when NetworkManager fails."""
        with patch('tidal_dl_ng.download.NetworkManager') as mock_nm_class:
            with patch('tidal_dl_ng.download.requests.get') as mock_requests:
                # Make NetworkManager fail
                mock_nm = Mock()
                mock_response = MockResponse(success=False, error="Network error")
                mock_nm.make_request.return_value = mock_response
                mock_nm_class.return_value = mock_nm
                
                # Mock successful requests fallback
                mock_requests_response = Mock()
                mock_requests_response.text = "fallback content"
                mock_requests_response.url = "https://example.com/test"
                mock_requests.return_value = mock_requests_response
                
                client = RequestsClient()
                content, url = client.download("https://example.com/test")
                
                # Verify fallback was used
                mock_requests.assert_called_once()
                assert content == "fallback content"
    
    def test_download_cover_network_manager_usage(self):
        """Test that cover downloads use NetworkManager."""
        with patch('tidal_dl_ng.download.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_response = MockResponse(success=True, content=b"fake_image_data")
            mock_nm.make_request.return_value = mock_response
            mock_nm_class.return_value = mock_nm
            
            # Test cover_data static method
            result = Download.cover_data(url="https://example.com/cover.jpg")
            
            # Verify NetworkManager was used
            mock_nm.make_request.assert_called_once()
            assert result == b"fake_image_data"
    
    def test_download_cover_fallback_mechanism(self):
        """Test cover download fallback to direct requests."""
        with patch('tidal_dl_ng.download.NetworkManager') as mock_nm_class:
            with patch('tidal_dl_ng.download.requests.get') as mock_requests:
                # Make NetworkManager fail
                mock_nm = Mock()
                mock_response = MockResponse(success=False, error="Network error")
                mock_nm.make_request.return_value = mock_response
                mock_nm_class.return_value = mock_nm
                
                # Mock successful requests fallback
                mock_requests_response = Mock()
                mock_requests_response.content = b"fallback_image_data"
                mock_requests.return_value = mock_requests_response
                
                result = Download.cover_data(url="https://example.com/cover.jpg")
                
                # Verify fallback was used
                mock_requests.assert_called_once()
                assert result == b"fallback_image_data"


class TestAPIIntegration:
    """Test API module integration with NetworkManager."""
    
    def test_api_module_functions_exist(self):
        """Test that API module functions are available and working."""
        import tidal_dl_ng.api as api
        
        # Test that key functions exist and work
        assert hasattr(api, 'getNum')
        assert hasattr(api, 'getItem')
        assert hasattr(api, 'isItemValid')
        assert hasattr(api, 'getItems')
        
        # Test basic functionality
        num_keys = api.getNum()
        assert isinstance(num_keys, int)
        assert num_keys > 0
        
        # Test getting an item
        item = api.getItem(0)
        assert isinstance(item, dict)
        assert 'clientId' in item
        assert 'clientSecret' in item
    
    def test_api_network_manager_integration(self):
        """Test that API module can work with NetworkManager (integration test)."""
        # This is more of a smoke test - we verify the API module loaded successfully
        # and that NetworkManager can be instantiated alongside it
        import tidal_dl_ng.api as api
        from tidal_dl_ng.network import NetworkManager
        
        # Both should be importable and functional
        network_manager = NetworkManager()
        assert hasattr(network_manager, 'get_json')
        
        # API should have loaded keys (either from network or fallback)
        keys = api.getItems()
        assert isinstance(keys, list)
        assert len(keys) > 0


class TestTidalIntegration:
    """Test Tidal class integration with NetworkManager."""
    
    def test_tidal_session_injection(self, mock_network_manager, mock_tidal_session, test_settings):
        """Test that Tidal class properly injects NetworkManager session."""
        mock_auth_session = Mock()
        mock_network_manager.get_session.return_value = mock_auth_session
        
        # Create Tidal instance
        tidal = Tidal(test_settings)
        
        # Verify session injection was attempted
        assert hasattr(tidal, '_inject_network_manager')
        assert tidal.session.request_session == mock_auth_session
    
    def test_tidal_session_integrity_monitoring(self, mock_network_manager, mock_tidal_session):
        """Test session integrity monitoring in Tidal class."""
        mock_auth_session = Mock()
        mock_network_manager.get_session.return_value = mock_auth_session
        
        tidal = Tidal()
        
        # Test monitoring method exists
        assert hasattr(tidal, '_monitor_session_integrity')
        assert callable(tidal._monitor_session_integrity)
        
        # Test monitoring functionality
        original_session = tidal.session.request_session
        new_session = Mock()
        tidal.session.request_session = new_session
        
        # Call monitoring
        tidal._monitor_session_integrity()
        
        # Should re-inject NetworkManager session
        assert tidal.session.request_session == mock_auth_session
    
    def test_tidal_proxy_error_handling(self, mock_tidal_session):
        """Test proxy-specific error handling in Tidal class."""
        tidal = Tidal()
        
        # Test error handling method exists
        assert hasattr(tidal, '_handle_authentication_error')
        assert callable(tidal._handle_authentication_error)


class TestSettingsIntegration:
    """Test Settings class integration with NetworkManager."""
    
    def test_settings_network_manager_configuration(self):
        """Test that Settings properly configures NetworkManager."""
        # Create settings and verify NetworkManager is configured
        settings = Settings()
        network_manager = NetworkManager()
        
        # Check if NetworkManager has configuration
        is_configured = network_manager.is_configured()
        
        # Configuration is optional, so we just verify the method exists
        assert hasattr(network_manager, 'is_configured')
        assert isinstance(is_configured, bool)
    
    def test_settings_automatic_network_manager_setup(self, network_settings, proxy_settings):
        """Test that Settings automatically sets up NetworkManager."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm_class.return_value = mock_nm
            
            # Create settings
            settings = Settings()
            settings.data.network_settings = network_settings
            settings.data.proxy_settings = proxy_settings
            
            # Save settings (should trigger NetworkManager configuration)
            settings.save()
            
            # Verify NetworkManager configure was called
            mock_nm.configure.assert_called()


class TestCompleteIntegration:
    """Test complete integration scenarios."""
    
    def test_end_to_end_integration(self, network_settings, proxy_settings, mock_tidal_session, temp_directory, mock_logger):
        """Test end-to-end integration with all components."""
        # Configure NetworkManager
        network_manager = NetworkManager()
        network_manager.configure(network_settings, proxy_settings)
        
        # Create Settings with network configuration
        settings = Settings()
        settings.data.network_settings = network_settings
        settings.data.proxy_settings = proxy_settings
        
        # Create Tidal instance
        tidal = Tidal(settings)
        
        # Create Download instance
        download = Download(
            session=mock_tidal_session,
            path_base=str(temp_directory),
            fn_logger=mock_logger
        )
        
        # Verify all components are properly integrated
        assert network_manager.is_configured()
        assert network_manager.is_proxy_enabled() == proxy_settings.enabled
        assert tidal.session.request_session == network_manager.get_session("auth")
        assert hasattr(download, 'network_manager')
    
    def test_integration_with_disabled_proxy(self, network_settings, disabled_proxy_settings, mock_tidal_session):
        """Test integration when proxy is disabled."""
        # Configure NetworkManager with disabled proxy
        network_manager = NetworkManager()
        network_manager.configure(network_settings, disabled_proxy_settings)
        
        # Create Tidal instance
        tidal = Tidal()
        
        # Verify integration works with disabled proxy
        assert network_manager.is_configured()
        assert not network_manager.is_proxy_enabled()
        assert tidal.session.request_session == network_manager.get_session("auth")
    
    def test_fallback_chain_integration(self):
        """Test that fallback mechanisms work across all components."""
        with patch('tidal_dl_ng.download.NetworkManager') as mock_download_nm:
            with patch('tidal_dl_ng.download.requests.get') as mock_download_requests:
                
                # Make NetworkManager fail
                mock_download_nm.return_value.make_request.return_value = MockResponse(success=False)
                
                # Mock successful fallback
                mock_download_response = Mock()
                mock_download_response.content = b"download_fallback"
                mock_download_requests.return_value = mock_download_response
                
                # Test Download fallback
                result = Download.cover_data(url="https://example.com/cover.jpg")
                assert result == b"download_fallback"
                mock_download_requests.assert_called()


class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""
    
    def test_network_error_propagation(self, configured_network_manager):
        """Test that network errors are properly propagated."""
        # Test with non-existent domain
        response = configured_network_manager.make_request(
            "https://this-domain-does-not-exist-12345.com",
            method="GET",
            timeout=(5, 5)
        )
        
        assert not response.success
        assert response.error is not None
    
    def test_timeout_error_handling(self, configured_network_manager):
        """Test timeout error handling."""
        # Test with very short timeout
        response = configured_network_manager.make_request(
            "https://httpbin.org/delay/10",  # 10 second delay
            method="GET",
            timeout=(1, 1)  # 1 second timeout
        )
        
        assert not response.success
        assert response.error is not None
    
    def test_proxy_error_integration(self, network_settings):
        """Test proxy error handling integration."""
        # Create proxy settings with invalid proxy
        from tidal_dl_ng.model.network import ProxySettings
        invalid_proxy_settings = ProxySettings(
            enabled=True,
            http_proxy="http://invalid-proxy.example.com:8080",
            https_proxy="https://invalid-proxy.example.com:8080"
        )
        
        network_manager = NetworkManager()
        network_manager.configure(network_settings, invalid_proxy_settings)
        
        # Test that proxy errors are handled gracefully
        response = network_manager.make_request(
            "https://httpbin.org/get",
            method="GET",
            timeout=(5, 5)
        )
        
        # Should fail gracefully with proxy error
        assert not response.success
        assert response.error is not None


class TestPerformanceIntegration:
    """Test performance aspects of integration."""
    
    def test_session_caching_integration(self, configured_network_manager):
        """Test that session caching works across components."""
        # Get sessions multiple times
        session1 = configured_network_manager.get_session("download")
        session2 = configured_network_manager.get_session("download")
        session3 = configured_network_manager.get_session("api")
        session4 = configured_network_manager.get_session("api")
        
        # Same session types should return same instances
        assert session1 is session2
        assert session3 is session4
        
        # Different session types should be different instances
        assert session1 is not session3
    
    def test_connection_pooling_integration(self, configured_network_manager):
        """Test that connection pooling is properly configured."""
        session = configured_network_manager.get_session("download")
        
        # Verify session has adapters (connection pooling)
        assert len(session.adapters) > 0
        
        # Verify adapters are HTTPAdapter instances
        from requests.adapters import HTTPAdapter
        for adapter in session.adapters.values():
            assert isinstance(adapter, HTTPAdapter)
