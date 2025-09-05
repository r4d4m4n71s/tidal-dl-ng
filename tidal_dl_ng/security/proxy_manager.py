"""
proxy_manager.py

Manages proxy configuration and provides proxy settings for network requests.
Supports HTTP, HTTPS, and SOCKS5 proxies with authentication.

Classes:
    ProxyManager: Centralized proxy configuration manager.
"""

from typing import Dict, Optional

from tidal_dl_ng.model.cfg import Settings


class ProxyManager:
    """Manages proxy configuration and provides proxy settings for requests."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the proxy manager.

        Args:
            settings: Settings object containing proxy configuration.
        """
        self.settings = settings or Settings()

    def get_proxies(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration dictionary for requests.

        Returns:
            Dictionary with proxy settings or None if proxy is disabled.
        """
        if not self.settings.data.proxy_enabled:
            return None

        proxy_host = self.settings.data.proxy_host.strip()
        proxy_port = self.settings.data.proxy_port

        if not proxy_host:
            return None

        # Build proxy URL
        proxy_url = self._build_proxy_url(proxy_host, proxy_port)

        # Create proxy dictionary based on proxy type
        proxy_type = self.settings.data.proxy_type.strip().upper()
        
        if proxy_type == "SOCKS5":
            # For SOCKS5, we need to use socks5h:// to ensure DNS resolution through proxy
            return {
                "http": f"socks5h://{proxy_url}",
                "https": f"socks5h://{proxy_url}"
            }
        elif proxy_type == "HTTP":
            # Only HTTP proxy
            return {
                "http": f"http://{proxy_url}"
            }
        elif proxy_type == "HTTPS":
            # Only HTTPS proxy
            return {
                "https": f"https://{proxy_url}"
            }
        elif not proxy_type or proxy_type in ("HTTP|HTTPS", "HTTPS|HTTP"):
            # Empty proxy_type or explicit both - use proxy for both protocols
            return {
                "http": f"http://{proxy_url}",
                "https": f"https://{proxy_url}"
            }
        else:
            # Any other value defaults to both (backward compatibility)
            return {
                "http": f"http://{proxy_url}",
                "https": f"https://{proxy_url}"
            }

    def _build_proxy_url(self, host: str, port: int) -> str:
        """Build proxy URL with optional authentication.

        Args:
            host: Proxy hostname or IP address.
            port: Proxy port number.

        Returns:
            Proxy URL string.
        """
        if self.settings.data.proxy_use_auth:
            username = self.settings.data.proxy_username
            password = self.settings.data.proxy_password
            
            if username and password:
                # URL encode username and password for special characters
                import urllib.parse
                username = urllib.parse.quote(username, safe='')
                password = urllib.parse.quote(password, safe='')
                return f"{username}:{password}@{host}:{port}"
        
        return f"{host}:{port}"

    def get_verify_ssl(self) -> bool:
        """Get SSL verification setting for proxy connections.

        Returns:
            True to verify SSL certificates, False otherwise.
        """
        # For development/testing with self-signed certificates, this could be False
        # But for production, it should always be True
        return True

    def test_proxy_connection(self, test_url: str = "https://api.tidal.com") -> bool:
        """Test proxy connection.

        Args:
            test_url: URL to test the proxy connection against.

        Returns:
            True if proxy connection successful, False otherwise.
        """
        import requests
        
        proxies = self.get_proxies()
        if not proxies:
            return True  # No proxy configured, so "success"
        
        try:
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=10,
                verify=self.get_verify_ssl()
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Proxy connection test failed: {e}")
            return False

    def get_request_kwargs(self) -> Dict[str, any]:
        """Get all proxy-related kwargs for requests.

        Returns:
            Dictionary with proxy settings for requests.
        """
        kwargs = {}
        
        proxies = self.get_proxies()
        if proxies:
            kwargs['proxies'] = proxies
            kwargs['verify'] = self.get_verify_ssl()
        
        return kwargs
