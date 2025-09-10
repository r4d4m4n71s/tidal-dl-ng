"""Network-specific exceptions for TIDAL downloader.

This module defines custom exceptions for network operations, proxy handling,
and connection management.
"""


class ProxyConnectionError(Exception):
    """Exception raised when proxy connection fails.
    
    This exception is raised when:
    - Proxy server is unreachable
    - Proxy authentication fails
    - Proxy configuration is invalid
    """
    
    def __init__(self, message: str, proxy_url: str | None = None) -> None:
        """Initialize ProxyConnectionError.
        
        Args:
            message: Error description
            proxy_url: The proxy URL that failed (if available)
        """
        super().__init__(message)
        self.proxy_url = proxy_url


class NetworkTimeoutError(Exception):
    """Exception raised when network operations timeout.
    
    This exception is raised when:
    - Connection timeout is exceeded
    - Read timeout is exceeded
    - Request takes longer than configured limits
    """
    
    def __init__(self, message: str, timeout_value: float | None = None) -> None:
        """Initialize NetworkTimeoutError.
        
        Args:
            message: Error description
            timeout_value: The timeout value that was exceeded (if available)
        """
        super().__init__(message)
        self.timeout_value = timeout_value


class NetworkRetryExhaustedError(Exception):
    """Exception raised when all retry attempts are exhausted.
    
    This exception is raised when:
    - Maximum retry attempts are reached
    - Request continues to fail after all retries
    """
    
    def __init__(self, message: str, retry_count: int, last_error: Exception | None = None) -> None:
        """Initialize NetworkRetryExhaustedError.
        
        Args:
            message: Error description
            retry_count: Number of retries that were attempted
            last_error: The last exception that occurred before giving up
        """
        super().__init__(message)
        self.retry_count = retry_count
        self.last_error = last_error


class ProxyAuthenticationError(ProxyConnectionError):
    """Exception raised when proxy authentication fails during TIDAL operations.
    
    This exception is raised when:
    - Proxy requires authentication but credentials are invalid
    - Proxy authentication fails during login process
    - Authentication timeout occurs through proxy
    """
    
    def __init__(self, proxy_url: str, auth_stage: str, original_error: Exception) -> None:
        """Initialize ProxyAuthenticationError.
        
        Args:
            proxy_url: The proxy URL where authentication failed
            auth_stage: Stage where authentication failed ('connection', 'tidal_login', 'token_refresh')
            original_error: The original exception that caused the authentication failure
        """
        message = f"Proxy authentication failed during {auth_stage} through {proxy_url}"
        super().__init__(message, proxy_url)
        self.auth_stage = auth_stage
        self.original_error = original_error
