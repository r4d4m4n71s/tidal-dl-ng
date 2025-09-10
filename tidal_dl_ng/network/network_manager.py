"""Central network manager for TIDAL downloader.

This module provides the main NetworkManager singleton that coordinates
all network operations with proxy support, retry mechanisms, and robust
error handling.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union

import requests
from requests.exceptions import RequestException

from ..helper.decorator import SingletonMeta
from ..model.network import NetworkSettings, ProxySettings, NetworkResponse
from .proxy_manager import ProxyManager
from .http_client_factory import HttpClientFactory
from .retry_strategy import RetryStrategy
from .exceptions import NetworkTimeoutError, NetworkRetryExhaustedError


logger = logging.getLogger(__name__)


class NetworkManager(metaclass=SingletonMeta):
    """Central network manager for all HTTP operations.
    
    This singleton class provides:
    - Centralized network configuration
    - Proxy support with connection testing
    - Retry mechanisms with exponential backoff
    - File download with resume capability
    - JSON API request handling
    - Connectivity testing
    """
    
    def __init__(self) -> None:
        """Initialize NetworkManager with default settings."""
        self._network_settings = NetworkSettings()
        self._proxy_manager = ProxyManager()
        self._http_factory = HttpClientFactory(self._network_settings, self._proxy_manager)
        self._retry_strategy = RetryStrategy(self._network_settings)
        self._initialized = False
        self._session_cache = {}  # Cache for reusing sessions
        
        logger.info("NetworkManager initialized")
    
    def configure(
        self, 
        network_settings: NetworkSettings,
        proxy_settings: Optional[ProxySettings] = None
    ) -> None:
        """Configure network manager with settings.
        
        Args:
            network_settings: Network configuration
            proxy_settings: Proxy configuration (optional)
        """
        self._network_settings = network_settings
        self._retry_strategy = RetryStrategy(network_settings)
        
        if proxy_settings:
            self._proxy_manager.configure(proxy_settings)
        
        # Update factory with new settings
        self._http_factory.update_settings(
            network_settings=network_settings,
            proxy_manager=self._proxy_manager
        )
        
        self._initialized = True
        logger.info("NetworkManager configured with new settings")
    
    def make_request(
        self, 
        url: str, 
        method: str = "GET",
        **kwargs
    ) -> NetworkResponse:
        """Make HTTP request with retry logic.
        
        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests
            
        Returns:
            NetworkResponse with request results
        """
        if not self._initialized:
            logger.warning("NetworkManager not configured, using default settings")
        
        attempt = 0
        last_response = None
        
        while attempt <= self._network_settings.retry_attempts:
            try:
                # Create session for this request
                session = self._http_factory.create_session()
                
                # Make the request
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = session.request(method, url, **kwargs)
                
                # Create successful response
                network_response = NetworkResponse(
                    success=True,
                    status_code=response.status_code,
                    content=response.content,
                    error=None,
                    retry_count=attempt
                )
                
                # Check if response indicates success
                if 200 <= response.status_code < 300:
                    logger.debug(f"Request successful: {response.status_code}")
                    return network_response
                else:
                    # Non-success status code
                    network_response.success = False
                    logger.warning(f"Request returned status {response.status_code}")
                
                last_response = network_response
                
            except RequestException as e:
                logger.warning(f"Request failed: {e}")
                
                # Create error response
                network_response = NetworkResponse(
                    success=False,
                    status_code=None,
                    content=None,
                    error=e,
                    retry_count=attempt
                )
                
                last_response = network_response
            
            except Exception as e:
                logger.error(f"Unexpected error during request: {e}")
                
                network_response = NetworkResponse(
                    success=False,
                    status_code=None,
                    content=None,
                    error=e,
                    retry_count=attempt
                )
                
                last_response = network_response
            
            # Check if we should retry
            if self._retry_strategy.should_retry(last_response, attempt):
                self._retry_strategy.wait_for_retry(attempt)
                attempt += 1
            else:
                break
        
        # All retries exhausted
        if last_response and not last_response.success:
            logger.error(f"Request failed after {attempt} attempts")
            
            # If we exhausted retries, wrap in retry exhausted error
            if attempt >= self._network_settings.retry_attempts:
                retry_error = self._retry_strategy.create_retry_exhausted_error(
                    last_response, attempt
                )
                last_response.error = retry_error
        
        return last_response or NetworkResponse(
            success=False,
            status_code=None,
            content=None,
            error=Exception("Unknown error occurred"),
            retry_count=attempt
        )
    
    def download_file(
        self, 
        url: str, 
        file_path: Path,
        resume: bool = True,
        chunk_size: int = 8192
    ) -> NetworkResponse:
        """Download file with resume capability.
        
        Args:
            url: URL to download from
            file_path: Path to save file
            resume: Whether to resume partial downloads
            chunk_size: Size of chunks to download
            
        Returns:
            NetworkResponse with download results
        """
        headers = {}
        mode = 'wb'
        initial_pos = 0
        
        # Check if file exists and resume is enabled
        if resume and file_path.exists():
            initial_pos = file_path.stat().st_size
            headers['Range'] = f'bytes={initial_pos}-'
            mode = 'ab'
            logger.info(f"Resuming download from byte {initial_pos}")
        
        # Make request with streaming
        response = self.make_request(
            url, 
            method="GET",
            headers=headers,
            stream=True
        )
        
        if not response.success:
            return response
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file in chunks
            with open(file_path, mode) as f:
                if hasattr(response.content, 'iter_content'):
                    # If we have a streaming response
                    for chunk in response.content.iter_content(chunk_size=chunk_size):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                else:
                    # If we have the full content
                    f.write(response.content)
            
            logger.info(f"File downloaded successfully: {file_path}")
            
            # Update response to indicate successful download
            response.content = str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to write downloaded file: {e}")
            response.success = False
            response.error = e
        
        return response
    
    def get_json(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get JSON response from URL.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for request
            
        Returns:
            Parsed JSON data or None if failed
        """
        response = self.make_request(url, method="GET", **kwargs)
        
        if not response.success:
            logger.error(f"Failed to get JSON from {url}: {response.error}")
            return None
        
        try:
            if isinstance(response.content, bytes):
                json_data = response.content.decode('utf-8')
            else:
                json_data = response.content
            
            import json
            return json.loads(json_data)
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def post_json(
        self, 
        url: str, 
        data: Dict[str, Any],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Post JSON data and get JSON response.
        
        Args:
            url: URL to post to
            data: Data to post as JSON
            **kwargs: Additional arguments for request
            
        Returns:
            Parsed JSON response or None if failed
        """
        import json
        
        # Prepare JSON data
        json_data = json.dumps(data)
        headers = kwargs.get('headers', {})
        headers['Content-Type'] = 'application/json'
        kwargs['headers'] = headers
        
        response = self.make_request(
            url, 
            method="POST",
            data=json_data,
            **kwargs
        )
        
        if not response.success:
            logger.error(f"Failed to post JSON to {url}: {response.error}")
            return None
        
        try:
            if isinstance(response.content, bytes):
                json_response = response.content.decode('utf-8')
            else:
                json_response = response.content
            
            return json.loads(json_response)
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def test_connectivity(self) -> bool:
        """Test internet connectivity.
        
        Returns:
            True if connectivity test passes, False otherwise
        """
        return self._http_factory.test_connectivity()
    
    def validate_proxy(self) -> tuple[bool, str]:
        """Validate current proxy configuration.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        return self._proxy_manager.validate_current_proxy()
    
    def get_session(self, session_type: str = "default") -> requests.Session:
        """Get a configured session for direct use.
        
        Args:
            session_type: Type of session ("default", "download", "api", "auth")
            
        Returns:
            Configured requests.Session
        """
        # Check if we have a cached session
        if session_type in self._session_cache:
            return self._session_cache[session_type]
        
        # Create new session and cache it
        if session_type == "download":
            session = self._http_factory.create_download_session()
        elif session_type == "api":
            session = self._http_factory.create_api_session()
        elif session_type == "auth":
            session = self._http_factory.create_auth_session()
        else:
            session = self._http_factory.create_session()
        
        # Cache the session for reuse
        self._session_cache[session_type] = session
        return session
    
    def is_configured(self) -> bool:
        """Check if NetworkManager is properly configured.
        
        Returns:
            True if configured, False otherwise
        """
        return self._initialized
    
    def get_network_settings(self) -> NetworkSettings:
        """Get current network settings.
        
        Returns:
            Current NetworkSettings object
        """
        return self._network_settings
    
    def is_proxy_enabled(self) -> bool:
        """Check if proxy is currently enabled.
        
        Returns:
            True if proxy is enabled, False otherwise
        """
        return self._proxy_manager.is_proxy_enabled()
