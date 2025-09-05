"""
Shared pytest fixtures and configuration for tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Save current environment
    original_env = dict(os.environ)
    
    # Clear security-related environment variables
    security_vars = [
        'TIDAL_CLIENT_ID',
        'TIDAL_CLIENT_SECRET', 
        'TIDAL_MASTER_KEY',
        'TIDAL_USE_SECURE_DECRYPTION',
        'TIDAL_DL_NG_DEBUG'
    ]
    
    for var in security_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_settings():
    """Provide a mock settings object."""
    from unittest.mock import MagicMock
    from tidal_dl_ng.model.cfg import Settings as ModelSettings
    
    settings = MagicMock()
    settings.data = ModelSettings()
    
    # Set some defaults
    settings.data.proxy_enabled = False
    settings.data.download_delay = False
    settings.data.download_delay_sec_min = 3.0
    settings.data.download_delay_sec_max = 5.0
    
    return settings


@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide a temporary configuration directory."""
    config_dir = tmp_path / ".tidal-dl-ng"
    config_dir.mkdir()
    return config_dir


# Add markers for different test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )
    config.addinivalue_line(
        "markers", "vulnerability: mark test as tracking a known vulnerability"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
