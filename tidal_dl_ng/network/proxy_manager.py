"""Proxy management and connection testing for TIDAL downloader.

This module provides proxy configuration validation, connection testing,
and proxy authentication handling.
"""

import logging
from urllib.parse import urlparse
from typing import Dict, Tuple, Optional

import requests
from requests.auth import HTTPProxyAuth
from requests.exceptions import RequestException, ProxyError, ConnectTimeout

from ..helper.decorator import SingletonMeta
from ..model.network import ProxySettings
from .exceptions import ProxyConnectionError, NetworkTimeoutError


logger = logging.getLogger(__name__)


class ProxyManager(metaclass=SingletonMeta):
    """Manages proxy configuration and connection testing.
    
    This singleton class provides:
    - Proxy URL validation
    - Connection testing with timeout handling
    - Proxy authentication setup
    - Requests-compatible proxy configuration
    """
    
    def __init__(self) -> None:
        """Initialize ProxyManager."""
        self._current_settings: Optional[ProxySettings] = None
        self._validated_proxies: Dict[str, bool] = {}
    
    def configure(self, proxy_settings: ProxySettings) -> None:
        """Configure proxy settings.
        
        Args:
            proxy_settings: Proxy configuration to use
        """
        self._current_settings = proxy_settings
        # Clear validation cache when settings change
        self._validated_proxies.clear()
        
        if proxy_settings.enabled:
            logger.info("Proxy configuration updated and enabled")
        else:
            logger.info("Proxy configuration disabled")
    
    def validate_proxy_url(self, proxy_url: str) -> bool:
        """Validate proxy URL format.
        
        Args:
            proxy_url: Proxy URL to validate
            
        Returns:
            True if URL format is valid, False otherwise
        """
        if not proxy_url:
            return False
        
        try:
            parsed = urlparse(proxy_url)
            
            # Check if scheme is supported
            if parsed.scheme not in ('http', 'https'):
                logger.warning(f"Unsupported proxy scheme: {parsed.scheme}")
                return False
            
            # Check if hostname is present
            if not parsed.hostname:
                logger.warning("Proxy URL missing hostname")
                return False
            
            # Check if port is valid (if specified)
            if parsed.port is not None:
                if not (1 <= parsed.port <= 65535):
                    logger.warning(f"Invalid proxy port: {parsed.port}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Invalid proxy URL format: {e}")
            return False
    
    def test_proxy_connection(self, proxy_settings: ProxySettings) -> Tuple[bool, str]:
        """Test proxy connectivity using a simple HTTP request.
        
        Args:
            proxy_settings: Proxy configuration to test
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not proxy_settings.enabled:
            return True, "Proxy is disabled"
        
        # Validate proxy URLs first
        if proxy_settings.http_proxy and not self.validate_proxy_url(proxy_settings.http_proxy):
            return False, f"Invalid HTTP proxy URL: {proxy_settings.http_proxy}"
        
        if proxy_settings.https_proxy and not self.validate_proxy_url(proxy_settings.https_proxy):
            return False, f"Invalid HTTPS proxy URL: {proxy_settings.https_proxy}"
        
        # Create proxy configuration
        try:
            proxy_dict = self.create_proxy_dict(proxy_settings)
            auth = self.get_proxy_auth(proxy_settings)
            
            # Use the configured test URL
            test_url = proxy_settings.test_url
            
            # Create a test session
            session = requests.Session()
            session.proxies.update(proxy_dict)
            
            if auth:
                session.auth = auth
            
            # Test the connection
            logger.info(f"Testing proxy connection to {test_url}")
            response = session.get(
                test_url,
                timeout=proxy_settings.connection_timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                logger.info("Proxy connection test successful")
                # Cache successful validation
                proxy_key = f"{proxy_settings.http_proxy}:{proxy_settings.https_proxy}"
                self._validated_proxies[proxy_key] = True
                return True, "Proxy connection successful"
            else:
                message = f"Proxy test failed with status code: {response.status_code}"
                logger.warning(message)
                return False, message
                
        except ConnectTimeout:
            message = f"Proxy connection timeout after {proxy_settings.connection_timeout}s"
            logger.error(message)
            return False, message
            
        except ProxyError as e:
            message = f"Proxy connection error: {str(e)}"
            logger.error(message)
            return False, message
            
        except RequestException as e:
            message = f"Request failed through proxy: {str(e)}"
            logger.error(message)
            return False, message
            
        except Exception as e:
            message = f"Unexpected error testing proxy: {str(e)}"
            logger.error(message)
            return False, message
    
    def create_proxy_dict(self, proxy_settings: ProxySettings) -> Dict[str, str]:
        """Create requests-compatible proxy dictionary with embedded credentials.
        
        Args:
            proxy_settings: Proxy configuration
            
        Returns:
            Dictionary with proxy configuration for requests library
        """
        proxy_dict = {}
        
        if proxy_settings.enabled:
            # Embed credentials in proxy URLs if available
            http_proxy = self._embed_credentials_in_url(
                proxy_settings.http_proxy, 
                proxy_settings.username, 
                proxy_settings.password
            )
            https_proxy = self._embed_credentials_in_url(
                proxy_settings.https_proxy, 
                proxy_settings.username, 
                proxy_settings.password
            )
            
            if http_proxy:
                proxy_dict['http'] = http_proxy
            
            if https_proxy:
                proxy_dict['https'] = https_proxy
            elif http_proxy:
                # Use HTTP proxy for HTTPS if HTTPS proxy not specified
                proxy_dict['https'] = http_proxy
        
        return proxy_dict
    
    def get_proxy_auth(self, proxy_settings: ProxySettings) -> Optional[HTTPProxyAuth]:
        """Create proxy authentication object if credentials are provided.
        
        Args:
            proxy_settings: Proxy configuration
            
        Returns:
            HTTPProxyAuth object if credentials are provided, None otherwise
        """
        if (proxy_settings.enabled and 
            proxy_settings.username and 
            proxy_settings.password):
            return HTTPProxyAuth(proxy_settings.username, proxy_settings.password)
        
        return None
    
    def get_current_proxy_dict(self) -> Dict[str, str]:
        """Get proxy dictionary for current settings.
        
        Returns:
            Proxy dictionary for requests library
            
        Raises:
            ProxyConnectionError: If proxy is enabled but not configured
        """
        if not self._current_settings:
            return {}
        
        if not self._current_settings.enabled:
            return {}
        
        proxy_dict = self.create_proxy_dict(self._current_settings)
        
        if not proxy_dict:
            raise ProxyConnectionError("Proxy is enabled but no proxy URLs configured")
        
        return proxy_dict
    
    def get_current_proxy_auth(self) -> Optional[HTTPProxyAuth]:
        """Get proxy authentication for current settings.
        
        Returns:
            HTTPProxyAuth object if configured, None otherwise
        """
        if not self._current_settings:
            return None
        
        return self.get_proxy_auth(self._current_settings)
    
    def is_proxy_enabled(self) -> bool:
        """Check if proxy is currently enabled.
        
        Returns:
            True if proxy is enabled, False otherwise
        """
        return (self._current_settings is not None and 
                self._current_settings.enabled)
    
    def is_enabled(self) -> bool:
        """Alias for is_proxy_enabled() for backward compatibility.
        
        Returns:
            True if proxy is enabled, False otherwise
        """
        return self.is_proxy_enabled()
    
    def validate_current_proxy(self) -> Tuple[bool, str]:
        """Validate current proxy configuration.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self._current_settings:
            return True, "No proxy configured"
        
        return self.test_proxy_connection(self._current_settings)
    
    def _embed_credentials_in_url(self, proxy_url: str, username: str, password: str) -> str:
        """Embed credentials in proxy URL if available.
        
        Args:
            proxy_url: Original proxy URL
            username: Proxy username
            password: Proxy password
            
        Returns:
            Proxy URL with embedded credentials, or original URL if no credentials
        """
        if not proxy_url:
            return proxy_url
        
        if not username or not password:
            return proxy_url
        
        try:
            from urllib.parse import urlparse, urlunparse
            
            parsed = urlparse(proxy_url)
            
            # If credentials are already in the URL, don't modify it
            if parsed.username or parsed.password:
                return proxy_url
            
            # Embed credentials in the URL
            netloc = f"{username}:{password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            
            # Reconstruct URL with credentials
            new_parsed = parsed._replace(netloc=netloc)
            return urlunparse(new_parsed)
            
        except Exception as e:
            logger.warning(f"Failed to embed credentials in proxy URL: {e}")
            return proxy_url
