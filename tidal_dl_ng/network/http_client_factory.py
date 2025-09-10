"""HTTP client factory for creating configured requests sessions.

This module provides a factory for creating HTTP clients with appropriate
proxy configuration, timeouts, and other network settings.
"""

import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..model.network import NetworkSettings, ProxySettings
from .proxy_manager import ProxyManager


logger = logging.getLogger(__name__)


class HttpClientFactory:
    """Factory for creating configured HTTP clients.
    
    This class creates requests.Session objects with:
    - Proxy configuration
    - Timeout settings
    - User agent configuration
    - Connection pooling
    - SSL verification settings
    """
    
    def __init__(
        self, 
        network_settings: NetworkSettings,
        proxy_manager: ProxyManager
    ) -> None:
        """Initialize HttpClientFactory.
        
        Args:
            network_settings: Network configuration
            proxy_manager: Proxy manager instance
        """
        self.network_settings = network_settings
        self.proxy_manager = proxy_manager
    
    def create_session(
        self, 
        custom_timeout: Optional[tuple[int, int]] = None,
        verify_ssl: bool = True
    ) -> requests.Session:
        """Create a configured requests session.
        
        Args:
            custom_timeout: Custom timeout tuple (connect_timeout, read_timeout)
            verify_ssl: Whether to verify SSL certificates
            
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()
        
        # Configure timeouts
        if custom_timeout:
            connect_timeout, read_timeout = custom_timeout
        else:
            connect_timeout = self.network_settings.connection_timeout
            read_timeout = self.network_settings.read_timeout
        
        # Set default timeout for all requests
        session.timeout = (connect_timeout, read_timeout)
        
        # Configure user agent
        session.headers.update({
            'User-Agent': self.network_settings.user_agent
        })
        
        # Configure proxy settings
        if self.proxy_manager.is_proxy_enabled():
            try:
                proxy_dict = self.proxy_manager.get_current_proxy_dict()
                session.proxies.update(proxy_dict)
                
                # Note: Proxy authentication is now embedded in the proxy URLs
                # No need to set session.auth for proxy authentication
                
                logger.debug(f"Session configured with proxy: {proxy_dict}")
                
            except Exception as e:
                logger.error(f"Failed to configure proxy for session: {e}")
                # Continue without proxy rather than failing
        
        # Configure SSL verification
        session.verify = verify_ssl
        
        # Configure connection pooling and adapters
        self._configure_adapters(session)
        
        logger.debug("HTTP session created with network configuration")
        return session
    
    def _configure_adapters(self, session: requests.Session) -> None:
        """Configure HTTP adapters for connection pooling and retries.
        
        Args:
            session: Session to configure
        """
        # Create retry strategy for connection-level retries
        # Note: This is different from our application-level retry strategy
        # This handles low-level connection issues
        retry_strategy = Retry(
            total=2,  # Keep this low since we have application-level retries
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        # Create HTTP adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Max connections per pool
            pool_block=False      # Don't block when pool is full
        )
        
        # Mount adapters for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    
    def create_download_session(self) -> requests.Session:
        """Create a session optimized for file downloads.
        
        Returns:
            Session configured for large file downloads
        """
        session = self.create_session()
        
        # Use download timeout for downloads
        session.timeout = (
            self.network_settings.connection_timeout,
            self.network_settings.download_timeout
        )
        
        # Configure headers for downloads
        session.headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        logger.debug("Download session created")
        return session
    
    def create_api_session(self) -> requests.Session:
        """Create a session optimized for API calls.
        
        Returns:
            Session configured for API requests
        """
        session = self.create_session()
        
        # Configure headers for API calls
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        logger.debug("API session created")
        return session
    
    def create_auth_session(self) -> requests.Session:
        """Create a session optimized for authentication operations.
        
        Returns:
            Session configured for TIDAL authentication with shorter timeouts
        """
        # Use API timeout for authentication operations
        auth_timeout = self.network_settings.get_timeout_for_operation('auth')
        
        session = self.create_session(
            custom_timeout=(self.network_settings.connection_timeout, auth_timeout)
        )
        
        # TODO: This code snipped is generatin error: "Unsupported Media Type","status":415,"detail":"Content-Type 'application/json' is not supported."
        # Configure headers for authentication
        #session.headers.update({
        #   'Accept': 'application/json',
        #  'Content-Type': 'application/json'
        #})
        
        logger.debug(f"Auth session created with {auth_timeout}s timeout")
        return session
    
    def test_connectivity(self, test_url: str = "https://httpbin.org/ip") -> bool:
        """Test internet connectivity using current configuration.
        
        Args:
            test_url: URL to test connectivity against
            
        Returns:
            True if connectivity test passes, False otherwise
        """
        try:
            session = self.create_session(custom_timeout=(5, 10))
            response = session.get(test_url, timeout=(5, 10))
            
            success = response.status_code == 200
            if success:
                logger.info("Connectivity test successful")
            else:
                logger.warning(f"Connectivity test failed with status: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    def update_settings(
        self, 
        network_settings: Optional[NetworkSettings] = None,
        proxy_manager: Optional[ProxyManager] = None
    ) -> None:
        """Update factory configuration.
        
        Args:
            network_settings: New network settings (optional)
            proxy_manager: New proxy manager (optional)
        """
        if network_settings:
            self.network_settings = network_settings
            logger.debug("Network settings updated in HttpClientFactory")
        
        if proxy_manager:
            self.proxy_manager = proxy_manager
            logger.debug("Proxy manager updated in HttpClientFactory")
