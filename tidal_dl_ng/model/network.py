"""Network-related data models for TIDAL downloader.

This module contains data structures for proxy configuration, network settings,
and network response handling.
"""

from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ProxySettings:
    """Configuration for HTTP/HTTPS proxy settings.
    
    Attributes:
        enabled: Whether proxy is enabled
        http_proxy: HTTP proxy URL (e.g., 'http://proxy.example.com:8080')
        https_proxy: HTTPS proxy URL (e.g., 'https://proxy.example.com:8080')
        username: Proxy authentication username
        password: Proxy authentication password
        connection_timeout: Timeout for proxy connection testing in seconds
        test_url: URL used to test proxy connectivity
    """
    enabled: bool = False
    http_proxy: str = ""
    https_proxy: str = ""
    username: str = ""
    password: str = ""
    connection_timeout: int = 10
    test_url: str = "https://httpbin.org/ip"


@dataclass_json
@dataclass
class NetworkSettings:
    """Configuration for network behavior and retry mechanisms.
    
    Attributes:
        retry_attempts: Maximum number of retry attempts for failed requests
        retry_backoff_factor: Multiplier for exponential backoff delay
        retry_max_delay: Maximum delay between retries in seconds
        connection_timeout: Timeout for establishing connections in seconds
        read_timeout: Timeout for reading response data in seconds
        download_timeout: Timeout for large file downloads in seconds
        api_timeout: Timeout for API calls and authentication in seconds
        user_agent: User agent string for HTTP requests
    """
    retry_attempts: int = 3
    retry_backoff_factor: float = 1.5
    retry_max_delay: float = 60.0
    connection_timeout: int = 5
    read_timeout: int = 45
    download_timeout: float = 30.0
    api_timeout: float = 10.0
    user_agent: str = "TIDAL/2.19.1 (Linux;Android 13; Android Auto) okhttp/4.10.0"

    def get_timeout_for_operation(self, operation_type: str) -> float:
        """Get appropriate timeout based on operation type.
        
        Args:
            operation_type: Type of operation ('download', 'api', 'auth', 'connection')
            
        Returns:
            Appropriate timeout value in seconds
        """
        timeouts = {
            'download': self.download_timeout,
            'api': self.api_timeout,
            'auth': self.api_timeout,  # Authentication uses API timeout
            'connection': self.connection_timeout
        }
        return timeouts.get(operation_type, self.api_timeout)


@dataclass
class NetworkResponse:
    """Response object for network operations.
    
    Attributes:
        success: Whether the request was successful
        status_code: HTTP status code (None if request failed before getting response)
        content: Response content (bytes for binary, str for text)
        error: Exception that occurred during request (None if successful)
        retry_count: Number of retries attempted for this request
    """
    success: bool
    status_code: int | None
    content: bytes | str | None
    error: Exception | None
    retry_count: int
