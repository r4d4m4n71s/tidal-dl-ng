"""Shared fixtures and utilities for network tests."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from tidal_dl_ng.network import NetworkManager, ProxyManager
from tidal_dl_ng.config import Settings, Tidal
from tidal_dl_ng.model.network import NetworkSettings, ProxySettings
from tests.network.credential_loader import get_proxy_settings, get_network_settings, get_test_api_keys_json, get_test_gist_response


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    # Reset all singleton instances to ensure clean test state
    NetworkManager._instances = {}
    ProxyManager._instances = {}
    Settings._instances = {}
    Tidal._instances = {}
    yield
    # Clean up after test
    NetworkManager._instances = {}
    ProxyManager._instances = {}
    Settings._instances = {}
    Tidal._instances = {}


@pytest.fixture
def network_settings():
    """Create test NetworkSettings instance from centralized credentials."""
    return get_network_settings("unit_tests")


@pytest.fixture
def proxy_settings():
    """Create test ProxySettings instance from centralized credentials."""
    return get_proxy_settings("test")


@pytest.fixture
def disabled_proxy_settings():
    """Create disabled ProxySettings instance from centralized credentials."""
    return get_proxy_settings("disabled")


@pytest.fixture
def temp_directory():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_tidal_session():
    """Create mock tidalapi.Session."""
    with patch('tidalapi.Session') as mock_session_class:
        mock_session = Mock()
        mock_session.request_session = Mock()
        mock_session.load_oauth_session.return_value = True
        mock_session.login_oauth_simple.return_value = True
        mock_session.check_login.return_value = True
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_network_manager():
    """Create mock NetworkManager."""
    with patch('tidal_dl_ng.config.NetworkManager') as mock_nm_class:
        mock_nm = Mock()
        mock_nm.is_configured.return_value = True
        mock_nm.is_proxy_enabled.return_value = True
        mock_session = Mock()
        mock_nm.get_session.return_value = mock_session
        mock_nm_class.return_value = mock_nm
        yield mock_nm


@pytest.fixture
def configured_network_manager(network_settings, disabled_proxy_settings):
    """Create configured NetworkManager instance with disabled proxy for unit tests."""
    nm = NetworkManager()
    nm.configure(network_settings, disabled_proxy_settings)
    return nm

@pytest.fixture
def mock_configured_network_manager(network_settings, disabled_proxy_settings):
    """Create mock NetworkManager for fast unit tests."""
    with patch('tidal_dl_ng.network.NetworkManager') as mock_nm_class:
        mock_nm = Mock()
        mock_nm.is_configured.return_value = True
        mock_nm.is_proxy_enabled.return_value = False
        mock_nm.get_network_settings.return_value = network_settings
        
        # Mock successful responses for all operations
        mock_response = MockResponse(success=True, status_code=200, content=b"test content")
        mock_nm.make_request.return_value = mock_response
        mock_nm.download_file.return_value = mock_response
        mock_nm.get_json.return_value = {"test": "data"}
        
        # Mock session creation
        mock_session = Mock()
        mock_session.timeout = (network_settings.connection_timeout, network_settings.api_timeout)
        mock_nm.get_session.return_value = mock_session
        
        mock_nm_class.return_value = mock_nm
        yield mock_nm


@pytest.fixture
def test_settings(network_settings, proxy_settings):
    """Create test Settings instance with network configuration."""
    settings = Settings()
    settings.data.network_settings = network_settings
    settings.data.proxy_settings = proxy_settings
    return settings


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, success=True, status_code=200, content=None, error=None):
        self.success = success
        self.status_code = status_code
        self.content = content or b"test content"
        self.error = error
        self.headers = {"content-type": "application/json"}
    
    def json(self):
        """Return JSON content."""
        if isinstance(self.content, dict):
            return self.content
        return {"test": "data"}


@pytest.fixture
def mock_successful_response():
    """Create mock successful HTTP response."""
    return MockResponse(success=True, status_code=200, content=b"success")


@pytest.fixture
def mock_failed_response():
    """Create mock failed HTTP response."""
    return MockResponse(success=False, status_code=500, error="Server Error")


def create_mock_tidal_with_token():
    """Helper to create Tidal instance with mock token data."""
    tidal = Mock()
    tidal.token_from_storage = True
    tidal.data = Mock()
    tidal.data.token_type = "Bearer"
    tidal.data.access_token = "test_token"
    tidal.data.refresh_token = "test_refresh"
    tidal.data.expiry_time = 1234567890
    return tidal


def assert_proxy_configured(session, proxy_settings):
    """Assert that session has proxy configuration."""
    assert session.proxies is not None
    if proxy_settings.enabled:
        assert session.proxies.get('http') == proxy_settings.http_proxy
        assert session.proxies.get('https') == proxy_settings.https_proxy


def assert_timeout_configured(session, expected_timeout):
    """Assert that session has correct timeout configuration."""
    if isinstance(expected_timeout, tuple):
        assert session.timeout == expected_timeout
    else:
        assert session.timeout == expected_timeout


class MockLogger:
    """Mock logger for testing that provides all expected methods."""
    
    def __init__(self):
        self.messages = []
    
    def info(self, msg):
        self.messages.append(('INFO', msg))
        print(f"INFO: {msg}")
    
    def warning(self, msg):
        self.messages.append(('WARNING', msg))
        print(f"WARNING: {msg}")
    
    def error(self, msg):
        self.messages.append(('ERROR', msg))
        print(f"ERROR: {msg}")
    
    def debug(self, msg):
        self.messages.append(('DEBUG', msg))
        print(f"DEBUG: {msg}")


@pytest.fixture
def mock_logger():
    """Create mock logger for tests."""
    return MockLogger()


# Test data constants from centralized credentials
TEST_API_KEYS_JSON = get_test_api_keys_json()
TEST_GIST_RESPONSE = get_test_gist_response()
