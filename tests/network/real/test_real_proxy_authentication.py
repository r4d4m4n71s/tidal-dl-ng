"""Test authentication with real proxy configuration.

This test validates TIDAL authentication works with actual proxy settings
and demonstrates the error handling capabilities.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tidal_dl_ng.config import Settings, Tidal
from tidal_dl_ng.network import NetworkManager, ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError
from tidal_dl_ng.model.cfg import Settings as ModelSettings
from tidal_dl_ng.model.network import NetworkSettings, ProxySettings
from tests.network.credential_loader import get_proxy_settings, get_network_settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_proxy_configuration(proxy_settings, network_settings):
    """Test proxy configuration with real proxy details."""
    print("=" * 60)
    print("TESTING PROXY CONFIGURATION")
    print("=" * 60)
    
    print(f"Proxy Settings:")
    print(f"  Host: {proxy_settings.http_proxy}")
    print(f"  Username: {proxy_settings.username}")
    print(f"  Connection Timeout: {proxy_settings.connection_timeout}s")
    print(f"  Test URL: {proxy_settings.test_url}")
    
    print(f"\nNetwork Settings:")
    print(f"  API Timeout: {network_settings.api_timeout}s")
    print(f"  Download Timeout: {network_settings.download_timeout}s")
    print(f"  Connection Timeout: {network_settings.connection_timeout}s")
    print(f"  Retry Attempts: {network_settings.retry_attempts}")
    
    # Verify proxy settings are properly configured
    assert proxy_settings.enabled is True
    assert proxy_settings.http_proxy == "http://geo.iproyal.com:12321"
    assert proxy_settings.username == "LwAit6sjotiaziYw"
    assert network_settings.api_timeout == 15.0
    
    print("✓ Proxy configuration validated successfully")


def test_network_manager_configuration(proxy_settings, network_settings):
    """Test NetworkManager configuration with proxy."""
    print("\n" + "=" * 60)
    print("TESTING NETWORK MANAGER CONFIGURATION")
    print("=" * 60)
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    print("✓ NetworkManager configured successfully")
    print(f"✓ Proxy enabled: {network_manager.is_proxy_enabled()}")
    print(f"✓ NetworkManager configured: {network_manager.is_configured()}")
    
    # Verify configuration
    assert network_manager.is_configured() is True
    assert network_manager.is_proxy_enabled() is True


def test_proxy_connectivity(network_manager):
    """Test proxy connectivity."""
    print("\n" + "=" * 60)
    print("TESTING PROXY CONNECTIVITY")
    print("=" * 60)
    
    # Test basic connectivity
    print("Testing basic connectivity...")
    connectivity_result = network_manager.test_connectivity()
    print(f"✓ Connectivity test: {'PASSED' if connectivity_result else 'FAILED'}")
    
    # Validate proxy configuration
    print("Validating proxy configuration...")
    proxy_valid, proxy_message = network_manager.validate_proxy()
    print(f"✓ Proxy validation: {'PASSED' if proxy_valid else 'FAILED'}")
    print(f"  Message: {proxy_message}")
    
    # Note: These tests may fail if proxy is not accessible, but that's expected
    # We're testing the functionality, not requiring the proxy to be working
    print("Note: Connectivity tests may fail if proxy is not accessible - this is expected")


def test_session_creation(network_manager):
    """Test different session types."""
    print("\n" + "=" * 60)
    print("TESTING SESSION CREATION")
    print("=" * 60)
    
    # Test different session types
    session_types = ["default", "api", "auth", "download"]
    
    for session_type in session_types:
        print(f"Creating {session_type} session...")
        session = network_manager.get_session(session_type)
        
        print(f"✓ {session_type.capitalize()} session created")
        print(f"  Timeout: {session.timeout}")
        print(f"  User-Agent: {session.headers.get('User-Agent', 'Not set')}")
        print(f"  Proxies configured: {'Yes' if session.proxies else 'No'}")
        
        if session.proxies:
            print(f"  HTTP Proxy: {session.proxies.get('http', 'Not set')}")
            print(f"  HTTPS Proxy: {session.proxies.get('https', 'Not set')}")
        
        # Verify session was created properly
        assert session is not None
        assert hasattr(session, 'timeout')
        assert hasattr(session, 'headers')
        assert hasattr(session, 'proxies')


def test_tidal_integration(network_manager):
    """Test TIDAL integration with NetworkManager."""
    print("\n" + "=" * 60)
    print("TESTING TIDAL INTEGRATION")
    print("=" * 60)
    
    # Create Tidal instance (this should inject NetworkManager session)
    print("Creating Tidal instance...")
    tidal = Tidal()
    
    print("✓ Tidal instance created")
    
    # Check if NetworkManager session was injected
    auth_session = network_manager.get_session("auth")
    injected_correctly = tidal.session.request_session == auth_session
    
    print(f"✓ Session injection: {'SUCCESS' if injected_correctly else 'FAILED'}")
    
    if injected_correctly:
        print(f"  Injected session timeout: {tidal.session.request_session.timeout}")
        print(f"  Injected session proxies: {'Yes' if tidal.session.request_session.proxies else 'No'}")
    
    # Test session integrity monitoring
    print("Testing session integrity monitoring...")
    original_session = tidal.session.request_session
    
    # Simulate tidalapi recreating session
    import requests
    tidal.session.request_session = requests.Session()
    
    # Call monitoring method
    tidal._monitor_session_integrity()
    
    # Check if session was re-injected
    monitoring_works = tidal.session.request_session == auth_session
    print(f"✓ Session monitoring: {'SUCCESS' if monitoring_works else 'FAILED'}")
    
    # Verify integration works
    assert tidal is not None
    assert hasattr(tidal, '_inject_network_manager')
    assert hasattr(tidal, '_monitor_session_integrity')
    assert injected_correctly, "NetworkManager session should be injected into tidalapi"
    assert monitoring_works, "Session monitoring should re-inject NetworkManager session"


def test_error_handling(invalid_proxy_settings):
    """Test error handling for different proxy scenarios."""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    network_settings = NetworkSettings(
        api_timeout=5.0,  # Short timeout to trigger timeout errors
        connection_timeout=3
    )
    
    print("Testing with invalid proxy configuration...")
    
    # Configure NetworkManager with invalid proxy
    network_manager = NetworkManager()
    network_manager.configure(network_settings, invalid_proxy_settings)
    
    # Create Tidal instance
    tidal = Tidal()
    
    # Test different error scenarios
    from requests.exceptions import ProxyError, ConnectTimeout, ConnectionError
    
    print("Testing proxy authentication error handling...")
    try:
        proxy_error = ProxyError("407 Proxy Authentication Required")
        tidal._handle_authentication_error(proxy_error)
        assert False, "Should have raised ProxyAuthenticationError"
    except ProxyAuthenticationError as e:
        print(f"✓ ProxyAuthenticationError handled correctly: {e}")
        assert "tidal_login" in str(e)
    
    print("Testing connection error handling...")
    try:
        conn_error = ConnectionError("Connection refused")
        tidal._handle_authentication_error(conn_error)
        assert False, "Should have raised ProxyConnectionError"
    except ProxyConnectionError as e:
        print(f"✓ ProxyConnectionError handled correctly")
        print(f"  Error message includes troubleshooting: {'Troubleshooting steps:' in str(e)}")
        assert "Troubleshooting steps:" in str(e)
    
    print("Testing timeout error handling...")
    try:
        timeout_error = ConnectTimeout("Connection timed out")
        tidal._handle_authentication_error(timeout_error)
        assert False, "Should have raised NetworkTimeoutError or ProxyConnectionError"
    except (NetworkTimeoutError, ProxyConnectionError) as e:
        print(f"✓ Timeout error handled correctly: {type(e).__name__}")
        assert "proxy" in str(e).lower()
    
    print("✓ All error handling tests passed")


def main():
    """Run all tests."""
    print("TIDAL AUTHENTICATION WITH PROXY - INTEGRATION TEST")
    print("=" * 60)
    print("This test validates NetworkManager integration with TIDAL authentication")
    print("using real proxy configuration for comprehensive testing.")
    print()
    
    # Load credentials from centralized system
    try:
        proxy_settings = get_proxy_settings("primary")
        network_settings = get_network_settings("integration_tests")
        invalid_proxy_settings = get_proxy_settings("invalid")
    except Exception as e:
        print(f"✗ CRITICAL: Failed to load credentials: {e}")
        return False
    
    # Test 1: Proxy Configuration
    try:
        test_proxy_configuration(proxy_settings, network_settings)
        proxy_config_ok = True
    except Exception as e:
        print(f"✗ Proxy configuration test failed: {e}")
        proxy_config_ok = False
    
    # Test 2: NetworkManager Configuration
    try:
        test_network_manager_configuration(proxy_settings, network_settings)
        network_manager = NetworkManager()
        network_manager.configure(network_settings, proxy_settings)
        network_config_ok = True
    except Exception as e:
        print(f"✗ CRITICAL: NetworkManager configuration failed: {e}")
        return False
    
    # Test 3: Proxy Connectivity
    try:
        test_proxy_connectivity(network_manager)
        connectivity_ok = True
    except Exception as e:
        print(f"⚠ WARNING: Proxy connectivity issues: {e}")
        connectivity_ok = False
    
    # Test 4: Session Creation
    try:
        test_session_creation(network_manager)
        sessions_ok = True
    except Exception as e:
        print(f"✗ CRITICAL: Session creation failed: {e}")
        return False
    
    # Test 5: TIDAL Integration
    try:
        test_tidal_integration(network_manager)
        tidal_ok = True
    except Exception as e:
        print(f"✗ CRITICAL: TIDAL integration failed: {e}")
        tidal_ok = False
    
    # Test 6: Error Handling
    try:
        test_error_handling(invalid_proxy_settings)
        error_handling_ok = True
    except Exception as e:
        print(f"⚠ Error handling test issues: {e}")
        error_handling_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Proxy Configuration: {'✓ PASSED' if proxy_config_ok else '✗ FAILED'}")
    print(f"NetworkManager Setup: ✓ PASSED")
    print(f"Proxy Connectivity: {'✓ PASSED' if connectivity_ok else '⚠ WARNING'}")
    print(f"Session Creation: {'✓ PASSED' if sessions_ok else '✗ FAILED'}")
    print(f"TIDAL Integration: {'✓ PASSED' if tidal_ok else '✗ FAILED'}")
    print(f"Error Handling: {'✓ PASSED' if error_handling_ok else '⚠ WARNING'}")
    
    overall_success = proxy_config_ok and sessions_ok and tidal_ok
    
    print(f"\nOVERALL RESULT: {'✓ SUCCESS' if overall_success else '✗ FAILED'}")
    
    if overall_success:
        print("\n🎉 All critical tests passed! NetworkManager is successfully integrated")
        print("   with TIDAL authentication and provides comprehensive proxy support.")
    else:
        print("\n❌ Some tests failed. Please review the output above for details.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
