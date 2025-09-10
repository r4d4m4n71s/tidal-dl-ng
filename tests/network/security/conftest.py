"""Fixtures for manual proxy authentication tests."""

import pytest
from tidal_dl_ng.network import NetworkManager
from tidal_dl_ng.model.network import NetworkSettings, ProxySettings
from tidal_dl_ng.config import Settings, Tidal
from tests.network.credential_loader import get_proxy_settings, get_network_settings


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    NetworkManager._instances = {}
    Settings._instances = {}
    Tidal._instances = {}
    yield
    # Clean up after test
    NetworkManager._instances = {}
    Settings._instances = {}
    Tidal._instances = {}


@pytest.fixture
def proxy_settings():
    """Create proxy settings for testing from centralized credentials."""
    return get_proxy_settings("primary")


@pytest.fixture
def network_settings():
    """Create network settings for testing from centralized credentials."""
    return get_network_settings("integration_tests")


@pytest.fixture
def network_manager(proxy_settings, network_settings):
    """Create and configure NetworkManager."""
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    return network_manager


@pytest.fixture
def invalid_proxy_settings():
    """Create invalid proxy settings for error testing from centralized credentials."""
    return get_proxy_settings("invalid")
