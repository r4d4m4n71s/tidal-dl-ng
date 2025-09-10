"""Network module for TIDAL downloader.

This module provides centralized network management with proxy support,
retry mechanisms, and robust error handling.
"""

from .network_manager import NetworkManager
from .proxy_manager import ProxyManager
from .exceptions import ProxyConnectionError, NetworkTimeoutError, NetworkRetryExhaustedError, ProxyAuthenticationError

__all__ = [
    "NetworkManager",
    "ProxyManager", 
    "ProxyConnectionError",
    "NetworkTimeoutError",
    "NetworkRetryExhaustedError",
    "ProxyAuthenticationError",
]
