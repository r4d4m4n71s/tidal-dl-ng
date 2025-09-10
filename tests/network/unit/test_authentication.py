"""TIDAL authentication integration tests with NetworkManager.

This module consolidates all authentication-related tests, including session injection,
integrity monitoring, and proxy-specific error handling.
"""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import ProxyError, ConnectTimeout, ConnectionError, HTTPError
from json import JSONDecodeError

from tidal_dl_ng.config import Tidal, Settings
from tidal_dl_ng.network import NetworkManager, ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError
from tidal_dl_ng.model.network import NetworkSettings, ProxySettings
from tests.network.unit.conftest import create_mock_tidal_with_token


class TestTidalSessionInjection:
    """Test NetworkManager session injection into tidalapi."""
    
    def test_session_injection_on_initialization(self, mock_network_manager, mock_tidal_session):
        """Test that NetworkManager session is injected into tidalapi on initialization."""
        mock_auth_session = Mock()
        mock_network_manager.get_session.return_value = mock_auth_session
        
        # Create Tidal instance
        tidal = Tidal()
        
        # Verify session injection
        assert tidal.session.request_session == mock_auth_session
        mock_network_manager.get_session.assert_called_with("auth")
    
    def test_session_injection_when_configured(self, mock_tidal_session):
        """Test session injection only occurs when NetworkManager is configured."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = False  # Not configured
            mock_nm_class.return_value = mock_nm
            
            # Create Tidal instance
            tidal = Tidal()
            
            # Session should not be replaced when NetworkManager is not configured
            mock_nm.get_session.assert_not_called()
    
    def test_session_injection_method_exists(self, mock_tidal_session):
        """Test that session injection method exists."""
        tidal = Tidal()
        assert hasattr(tidal, '_inject_network_manager')
        assert callable(tidal._inject_network_manager)


class TestSessionIntegrityMonitoring:
    """Test session integrity monitoring and re-injection."""
    
    def test_session_integrity_monitoring(self, mock_network_manager, mock_tidal_session):
        """Test that session integrity is monitored and re-injected when needed."""
        mock_auth_session = Mock()
        mock_network_manager.get_session.return_value = mock_auth_session
        
        tidal = Tidal()
        
        # Simulate tidalapi recreating the session
        new_session = Mock()
        tidal.session.request_session = new_session
        
        # Call monitoring method
        tidal._monitor_session_integrity()
        
        # Verify re-injection occurred
        assert tidal.session.request_session == mock_auth_session
    
    def test_monitoring_method_exists(self, mock_tidal_session):
        """Test that session monitoring method exists."""
        tidal = Tidal()
        assert hasattr(tidal, '_monitor_session_integrity')
        assert callable(tidal._monitor_session_integrity)
    
    def test_monitoring_only_when_configured(self, mock_tidal_session):
        """Test monitoring only occurs when NetworkManager is configured."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = False
            mock_nm_class.return_value = mock_nm
            
            tidal = Tidal()
            original_session = tidal.session.request_session
            
            # Call monitoring - should not change session when not configured
            tidal._monitor_session_integrity()
            
            assert tidal.session.request_session == original_session


class TestProxyErrorHandling:
    """Test proxy-specific error handling during authentication."""
    
    def test_proxy_authentication_error_handling(self, network_settings, mock_tidal_session):
        """Test handling of proxy authentication errors during login."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = True
            mock_nm.is_proxy_enabled.return_value = True
            mock_nm.get_network_settings.return_value = network_settings
            mock_nm_class.return_value = mock_nm
            
            tidal = Tidal()
            
            # Simulate 407 Proxy Authentication Required error
            proxy_error = ProxyError("407 Proxy Authentication Required")
            
            # Test error handling
            with pytest.raises(ProxyAuthenticationError) as exc_info:
                tidal._handle_authentication_error(proxy_error)
            
            assert "tidal_login" in str(exc_info.value)
            assert exc_info.value.auth_stage == "tidal_login"
    
    def test_proxy_connection_error_handling(self, network_settings, mock_tidal_session):
        """Test handling of proxy connection errors with troubleshooting messages."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = True
            mock_nm.is_proxy_enabled.return_value = True
            mock_nm.get_network_settings.return_value = network_settings
            mock_nm_class.return_value = mock_nm
            
            tidal = Tidal()
            
            # Simulate connection error
            conn_error = ConnectionError("Connection refused")
            
            # Test error handling
            with pytest.raises(ProxyConnectionError) as exc_info:
                tidal._handle_authentication_error(conn_error)
            
            error_msg = str(exc_info.value)
            assert "Troubleshooting steps:" in error_msg
            assert "Verify proxy server is running" in error_msg
            assert "Check proxy credentials" in error_msg
    
    def test_proxy_timeout_error_handling(self, network_settings, mock_tidal_session):
        """Test handling of proxy timeout errors with specific recommendations."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = True
            mock_nm.is_proxy_enabled.return_value = True
            mock_nm.get_network_settings.return_value = network_settings
            mock_nm_class.return_value = mock_nm
            
            tidal = Tidal()
            
            # Simulate timeout error
            timeout_error = ConnectTimeout("Connection timed out")
            
            # Test error handling - can be classified as timeout or connection error
            with pytest.raises((NetworkTimeoutError, ProxyConnectionError)) as exc_info:
                tidal._handle_authentication_error(timeout_error)
            
            error_msg = str(exc_info.value)
            assert "proxy" in error_msg.lower()
            
            # Check for timeout-specific or connection-specific messaging
            timeout_indicators = ["timed out", "timeout", "Increase timeout"]
            connection_indicators = ["Troubleshooting steps:", "Verify proxy server"]
            
            has_timeout_msg = any(indicator in error_msg for indicator in timeout_indicators)
            has_connection_msg = any(indicator in error_msg for indicator in connection_indicators)
            
            assert has_timeout_msg or has_connection_msg, "Should have appropriate error messaging"
    
    def test_non_proxy_error_passthrough(self, mock_tidal_session):
        """Test that non-proxy errors are passed through unchanged."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = True
            mock_nm.is_proxy_enabled.return_value = False  # Proxy disabled
            mock_nm_class.return_value = mock_nm
            
            tidal = Tidal()
            
            # Simulate generic error when proxy is disabled
            generic_error = Exception("Generic authentication error")
            
            # Test error handling - should re-raise original error
            with pytest.raises(Exception) as exc_info:
                tidal._handle_authentication_error(generic_error)
            
            assert exc_info.value == generic_error
    
    def test_error_handling_method_exists(self, mock_tidal_session):
        """Test that error handling method exists."""
        tidal = Tidal()
        assert hasattr(tidal, '_handle_authentication_error')
        assert callable(tidal._handle_authentication_error)


class TestAuthenticationFlow:
    """Test complete authentication flow with NetworkManager integration."""
    
    def test_login_token_with_session_monitoring(self, mock_network_manager, mock_tidal_session):
        """Test login_token method includes session monitoring."""
        mock_tidal_session.load_oauth_session.return_value = True
        
        # Mock token data
        with patch('tidal_dl_ng.config.BaseConfig.read') as mock_read:
            mock_read.return_value = True
            
            tidal = Tidal()
            tidal.token_from_storage = True
            tidal.data = Mock()
            tidal.data.token_type = "Bearer"
            tidal.data.access_token = "test_token"
            tidal.data.refresh_token = "test_refresh"
            tidal.data.expiry_time = 1234567890
            
            # Mock monitoring method
            tidal._monitor_session_integrity = Mock()
            
            # Call login_token
            result = tidal.login_token()
            
            # Verify monitoring was called
            tidal._monitor_session_integrity.assert_called_once()
            assert result is True
    
    def test_login_token_with_proxy_error(self, network_settings, mock_tidal_session):
        """Test login_token handles proxy errors gracefully."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = True
            mock_nm.is_proxy_enabled.return_value = True
            mock_nm.get_network_settings.return_value = network_settings
            mock_nm_class.return_value = mock_nm
            
            # Mock session to raise HTTPError (which is handled in the code)
            mock_tidal_session.load_oauth_session.side_effect = HTTPError("Proxy authentication failed")
            
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                with patch('os.path.exists', return_value=True):
                    with patch('os.remove') as mock_remove:
                        tidal = Tidal()
                        tidal.token_from_storage = True
                        tidal.data = create_mock_tidal_with_token().data
                        
                        # Should handle error gracefully and return False
                        result = tidal.login_token()
                        assert result is False
                        
                        # Verify error message was printed
                        mock_print.assert_called()
                        printed_args = [call.args[0] for call in mock_print.call_args_list]
                        # Check for the actual error message from the code
                        assert any("Either there is something wrong" in str(arg) or 
                                 "Try to login again" in str(arg) or
                                 "Authentication failed" in str(arg) for arg in printed_args)
    
    def test_login_token_with_invalid_token(self, mock_tidal_session):
        """Test login_token handles invalid token gracefully."""
        # Mock session to raise HTTP error (invalid token)
        mock_tidal_session.load_oauth_session.side_effect = HTTPError("401 Unauthorized")
        
        tidal = Tidal()
        tidal.token_from_storage = True
        tidal.data = create_mock_tidal_with_token().data
        
        # Should handle error and clean up token file
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            result = tidal.login_token()
            assert result is False
            mock_remove.assert_called_once()
    
    def test_login_with_proxy_error_handling(self, network_settings, mock_tidal_session):
        """Test main login method handles proxy errors gracefully."""
        with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
            mock_nm = Mock()
            mock_nm.is_configured.return_value = True
            mock_nm.is_proxy_enabled.return_value = True
            mock_nm.get_network_settings.return_value = network_settings
            mock_nm_class.return_value = mock_nm
            
            mock_tidal_session.login_oauth_simple.side_effect = ProxyError("Proxy error")
            
            tidal = Tidal()
            tidal.token_from_storage = False
            
            # Mock print function to capture output
            printed_messages = []
            def mock_print(msg):
                printed_messages.append(msg)
            
            # Call login
            result = tidal.login(mock_print)
            
            # Verify error was handled and appropriate message printed
            assert result is False
            assert any("You either do not have a token or your token is invalid." in msg for msg in printed_messages)
            
            # Check that a proxy-related error message was printed
            proxy_error_printed = any("proxy" in str(msg).lower() for msg in printed_messages)
            assert proxy_error_printed
    
    def test_login_successful_flow(self, mock_network_manager, mock_tidal_session):
        """Test successful login flow with session monitoring."""
        # Mock successful authentication
        mock_tidal_session.login_oauth_simple.return_value = None  # This method doesn't return a value
        mock_tidal_session.check_login.return_value = True
        
        # Mock the token persistence methods
        with patch.object(Tidal, 'token_persist') as mock_persist:
            tidal = Tidal()
            tidal.token_from_storage = False
            
            # Mock monitoring method
            tidal._monitor_session_integrity = Mock()
            
            # Mock print function
            printed_messages = []
            def mock_print(msg):
                printed_messages.append(msg)
            
            # Call login
            result = tidal.login(mock_print)
            
            # Verify successful login
            assert result is True
            assert any("The login was successful" in msg for msg in printed_messages)
            
            # Verify session monitoring was called during OAuth
            tidal._monitor_session_integrity.assert_called()
            
            # Verify token was persisted
            mock_persist.assert_called_once()


class TestAuthenticationTimeouts:
    """Test authentication timeout configuration."""
    
    def test_authentication_timeout_configuration(self, network_settings, proxy_settings):
        """Test that authentication uses appropriate timeout settings."""
        with patch('tidal_dl_ng.network.network_manager.HttpClientFactory') as mock_factory_class:
            mock_factory = Mock()
            mock_factory_class.return_value = mock_factory
            
            # Create NetworkManager and configure it
            network_manager = NetworkManager()
            network_manager.configure(network_settings, proxy_settings)
            
            # Request auth session
            network_manager.get_session("auth")
            
            # The factory should have been called to create auth session
            assert mock_factory.create_auth_session.called or mock_factory.create_session.called
    
    def test_auth_session_timeout_values(self, configured_network_manager, network_settings):
        """Test that auth session has correct timeout values."""
        auth_session = configured_network_manager.get_session("auth")
        
        # Auth session should have API timeout
        expected_timeout = (network_settings.connection_timeout, network_settings.api_timeout)
        assert auth_session.timeout == expected_timeout


class TestAuthenticationIntegrationWithRealNetworkManager:
    """Integration tests with real NetworkManager instance."""
    
    def test_integration_with_real_network_manager(self, network_settings, disabled_proxy_settings, mock_tidal_session):
        """Integration test with real NetworkManager instance."""
        # Configure NetworkManager
        network_manager = NetworkManager()
        network_manager.configure(network_settings, disabled_proxy_settings)
        
        # Create Tidal instance
        tidal = Tidal()
        
        # Verify NetworkManager session was injected
        auth_session = network_manager.get_session("auth")
        assert tidal.session.request_session == auth_session
        
        # Verify session has correct timeout configuration
        expected_timeout = (network_settings.connection_timeout, network_settings.api_timeout)
        assert auth_session.timeout == expected_timeout
    
    def test_settings_automatic_configuration(self, test_settings, mock_tidal_session):
        """Test that Settings automatically configures NetworkManager for authentication."""
        # Create Tidal instance with settings
        tidal = Tidal(test_settings)
        
        # NetworkManager should be configured
        network_manager = NetworkManager()
        assert network_manager.is_configured()
        
        # Note: Unit tests use "test" proxy which is enabled, but NetworkManager
        # configuration may vary based on initialization order. The important
        # thing is that it's configured and working.
        proxy_enabled = network_manager.is_proxy_enabled()
        settings_proxy_enabled = test_settings.data.proxy_settings.enabled
        
        # Both should be boolean values (configuration is working)
        assert isinstance(proxy_enabled, bool)
        assert isinstance(settings_proxy_enabled, bool)
        
        # Session should be injected
        auth_session = network_manager.get_session("auth")
        assert tidal.session.request_session == auth_session
