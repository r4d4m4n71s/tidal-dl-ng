"""Credential loader utility for centralized test authentication data.

This module provides utilities to load authentication credentials from a centralized
JSON file, eliminating duplication across test configuration files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from tidal_dl_ng.model.network import NetworkSettings, ProxySettings


class CredentialLoader:
    """Loads and provides centralized authentication credentials for tests."""
    
    def __init__(self, credentials_file: Optional[Path] = None):
        """Initialize credential loader.
        
        Args:
            credentials_file: Path to credentials JSON file. If None, uses default location.
        """
        if credentials_file is None:
            credentials_file = Path(__file__).parent / "credentials.json"
        
        self.credentials_file = credentials_file
        self._credentials: Optional[Dict[str, Any]] = None
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from JSON file with error handling."""
        if self._credentials is not None:
            return self._credentials
        
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                self._credentials = json.load(f)
            return self._credentials
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}. "
                "Ensure tests/network/credentials.json exists."
            )
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in credentials file {self.credentials_file}: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load credentials from {self.credentials_file}: {e}"
            )
    
    def get_proxy_settings(self, proxy_type: str = "primary") -> ProxySettings:
        """Get ProxySettings instance for specified proxy type.
        
        Args:
            proxy_type: Type of proxy configuration ("primary", "test", "invalid", "disabled")
            
        Returns:
            ProxySettings instance configured with specified proxy type
            
        Raises:
            KeyError: If proxy_type is not found in credentials
            ValueError: If proxy configuration is invalid
        """
        credentials = self._load_credentials()
        
        if proxy_type not in credentials["proxy"]:
            available_types = list(credentials["proxy"].keys())
            raise KeyError(
                f"Proxy type '{proxy_type}' not found. Available types: {available_types}"
            )
        
        proxy_config = credentials["proxy"][proxy_type]
        
        try:
            return ProxySettings(
                enabled=proxy_config.get("enabled", False),
                http_proxy=proxy_config.get("http_proxy"),
                https_proxy=proxy_config.get("https_proxy"),
                username=proxy_config.get("username"),
                password=proxy_config.get("password"),
                connection_timeout=proxy_config.get("connection_timeout", 10),
                test_url=proxy_config.get("test_url", "https://httpbin.org/ip")
            )
        except Exception as e:
            raise ValueError(
                f"Invalid proxy configuration for '{proxy_type}': {e}"
            )
    
    def get_network_settings(self, settings_type: str = "integration_tests") -> NetworkSettings:
        """Get NetworkSettings instance for specified settings type.
        
        Args:
            settings_type: Type of network settings ("unit_tests", "integration_tests")
            
        Returns:
            NetworkSettings instance configured with specified settings type
            
        Raises:
            KeyError: If settings_type is not found in credentials
            ValueError: If network configuration is invalid
        """
        credentials = self._load_credentials()
        
        if settings_type not in credentials["network"]:
            available_types = list(credentials["network"].keys())
            raise KeyError(
                f"Network settings type '{settings_type}' not found. Available types: {available_types}"
            )
        
        network_config = credentials["network"][settings_type]
        
        try:
            return NetworkSettings(
                retry_attempts=network_config.get("retry_attempts", 2),
                retry_backoff_factor=network_config.get("retry_backoff_factor", 1.5),
                retry_max_delay=network_config.get("retry_max_delay", 30.0),
                connection_timeout=network_config.get("connection_timeout", 10),
                read_timeout=network_config.get("read_timeout", 30),
                download_timeout=network_config.get("download_timeout", 60.0),
                api_timeout=network_config.get("api_timeout", 15.0),
                user_agent=network_config.get("user_agent", "Test Agent")
            )
        except Exception as e:
            raise ValueError(
                f"Invalid network configuration for '{settings_type}': {e}"
            )
    
    def get_tidal_test_api_keys(self) -> Dict[str, Any]:
        """Get TIDAL test API keys for unit testing.
        
        Returns:
            Dictionary containing test API key configuration
        """
        credentials = self._load_credentials()
        return credentials["tidal"]["test_api_keys"].copy()
    
    def get_tidal_environment_variables(self) -> Dict[str, str]:
        """Get TIDAL environment variable names for real credential testing.
        
        Returns:
            Dictionary mapping credential types to environment variable names
        """
        credentials = self._load_credentials()
        return credentials["tidal"]["environment_variables"].copy()
    
    def get_tidal_real_credentials(self) -> Dict[str, Any]:
        """Get real TIDAL credentials for authentication testing.
        
        Returns:
            Dictionary containing real TIDAL credentials
        """
        credentials = self._load_credentials()
        return credentials["tidal"]["real_credentials"].copy()
    
    def set_tidal_credentials_as_env_vars(self) -> None:
        """Set TIDAL credentials from JSON file as environment variables.
        
        This allows tests to use credentials from the JSON file without
        manually setting environment variables each time.
        """
        import os
        
        real_creds = self.get_tidal_real_credentials()
        
        # Set environment variables from JSON credentials
        if real_creds.get("username"):
            os.environ["TIDAL_USERNAME"] = real_creds["username"]
        
        if real_creds.get("password"):
            os.environ["TIDAL_PASSWORD"] = real_creds["password"]
        
        if real_creds.get("token"):
            os.environ["TIDAL_TOKEN"] = real_creds["token"]
        
        if real_creds.get("refresh_token"):
            os.environ["TIDAL_REFRESH_TOKEN"] = real_creds["refresh_token"]
    
    def get_credentials_info(self) -> Dict[str, Any]:
        """Get general information about the credentials file.
        
        Returns:
            Dictionary containing version and description information
        """
        credentials = self._load_credentials()
        return {
            "version": credentials.get("version", "unknown"),
            "description": credentials.get("description", ""),
            "file_path": str(self.credentials_file)
        }


# Global credential loader instance for convenience
_default_loader: Optional[CredentialLoader] = None


def get_credential_loader() -> CredentialLoader:
    """Get the default credential loader instance.
    
    Returns:
        CredentialLoader instance using default credentials file
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = CredentialLoader()
    return _default_loader


def get_proxy_settings(proxy_type: str = "primary") -> ProxySettings:
    """Convenience function to get proxy settings.
    
    Args:
        proxy_type: Type of proxy configuration
        
    Returns:
        ProxySettings instance
    """
    return get_credential_loader().get_proxy_settings(proxy_type)


def get_network_settings(settings_type: str = "integration_tests") -> NetworkSettings:
    """Convenience function to get network settings.
    
    Args:
        settings_type: Type of network settings
        
    Returns:
        NetworkSettings instance
    """
    return get_credential_loader().get_network_settings(settings_type)


def get_tidal_test_api_keys() -> Dict[str, Any]:
    """Convenience function to get TIDAL test API keys.
    
    Returns:
        Dictionary containing test API key configuration
    """
    return get_credential_loader().get_tidal_test_api_keys()


def get_tidal_environment_variables() -> Dict[str, str]:
    """Convenience function to get TIDAL environment variable names.
    
    Returns:
        Dictionary mapping credential types to environment variable names
    """
    return get_credential_loader().get_tidal_environment_variables()


def get_tidal_real_credentials() -> Dict[str, Any]:
    """Convenience function to get real TIDAL credentials.
    
    Returns:
        Dictionary containing real TIDAL credentials
    """
    return get_credential_loader().get_tidal_real_credentials()


def set_tidal_credentials_as_env_vars() -> None:
    """Convenience function to set TIDAL credentials as environment variables.
    
    This loads credentials from the JSON file and sets them as environment
    variables so tests can access them normally.
    """
    return get_credential_loader().set_tidal_credentials_as_env_vars()


# Test data constants for backward compatibility
def get_test_api_keys_json() -> Dict[str, Any]:
    """Get test API keys in the format expected by existing tests.
    
    Returns:
        Dictionary containing test API keys in legacy format
    """
    api_keys = get_tidal_test_api_keys()
    return {
        "version": "1.0.0",
        "keys": [api_keys]
    }


def get_test_gist_response() -> Dict[str, Any]:
    """Get test GIST response format for existing tests.
    
    Returns:
        Dictionary containing test GIST response format
    """
    api_keys_json = get_test_api_keys_json()
    return {
        "files": {
            "tidal-api-key.json": {
                "content": json.dumps(api_keys_json)
            }
        }
    }
