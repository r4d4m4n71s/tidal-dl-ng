"""
Proxy Management System for TIDAL Downloader Next Generation

This module provides comprehensive proxy support including:
- HTTP, HTTPS, and SOCKS5 proxy types
- Authentication with proper URL encoding
- Smart proxy selection based on request protocol
- Connection testing and validation
- Complete location masking for TIDAL requests
"""

import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPProxyAuth
from urllib3.util.retry import Retry

from tidal_dl_ng.constants import REQUESTS_TIMEOUT_SEC

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for a single proxy server."""
    name: str
    host: str
    port: int
    proxy_type: str  # http, https, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    protocols: List[str] = field(default_factory=lambda: ["http", "https"])
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    
    def __post_init__(self):
        """Validate proxy configuration after initialization."""
        if self.proxy_type.lower() not in ['http', 'https', 'socks5']:
            raise ValueError(f"Unsupported proxy type: {self.proxy_type}")
        
        if not self.host or not self.port:
            raise ValueError("Host and port are required")
            
        if self.port < 1 or self.port > 65535:
            raise ValueError("Port must be between 1 and 65535")

    @property
    def proxy_url(self) -> str:
        """Generate proxy URL with authentication."""
        if self.username and self.password:
            # URL encode username and password to handle special characters
            username = urllib.parse.quote(self.username, safe='')
            password = urllib.parse.quote(self.password, safe='')
            return f"{self.proxy_type}://{username}:{password}@{self.host}:{self.port}"
        else:
            return f"{self.proxy_type}://{self.host}:{self.port}"

    @property
    def proxy_dict(self) -> Dict[str, str]:
        """Generate proxy dictionary for requests library."""
        proxy_url = self.proxy_url
        proxy_dict = {}
        
        for protocol in self.protocols:
            proxy_dict[protocol] = proxy_url
            
        return proxy_dict

    def test_connection(self, timeout: int = 10) -> Tuple[bool, float, Optional[str]]:
        """
        Test proxy connection and measure latency.
        
        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "https://ifconfig.me/ip"
        ]
        
        for test_url in test_urls:
            try:
                start_time = time.time()
                
                session = requests.Session()
                session.proxies.update(self.proxy_dict)
                
                if self.username and self.password:
                    session.auth = HTTPProxyAuth(self.username, self.password)
                
                response = session.get(test_url, timeout=timeout)
                response.raise_for_status()
                
                latency = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                logger.info(f"Proxy {self.name} test successful. Latency: {latency:.2f}ms")
                return True, latency, None
                
            except Exception as e:
                logger.warning(f"Proxy {self.name} test failed with {test_url}: {str(e)}")
                continue
        
        error_msg = f"All test URLs failed for proxy {self.name}"
        logger.error(error_msg)
        return False, 0.0, error_msg


@dataclass
class ProxySettings:
    """Global proxy settings configuration."""
    enabled: bool = False
    proxies: List[ProxyConfig] = field(default_factory=list)
    auto_failover: bool = True
    test_timeout: int = 10
    health_check_interval: int = 300  # 5 minutes
    max_retries: int = 3
    retry_backoff_factor: float = 1.0


class ProxyManager:
    """
    Manages proxy configurations and provides proxy-aware HTTP sessions.
    
    Features:
    - Smart proxy selection based on protocol and performance
    - Automatic failover on proxy failures
    - Connection testing and health monitoring
    - Complete location masking for TIDAL requests
    """
    
    def __init__(self, settings: ProxySettings):
        self.settings = settings
        self.active_proxy: Optional[ProxyConfig] = None
        self.proxy_health: Dict[str, Tuple[bool, float]] = {}  # name -> (healthy, last_check)
        self._last_health_check = 0
        
        if self.settings.enabled and self.settings.proxies:
            self._select_best_proxy()

    def _select_best_proxy(self) -> Optional[ProxyConfig]:
        """Select the best available proxy based on priority and health."""
        if not self.settings.proxies:
            return None
            
        # Filter enabled proxies and sort by priority
        available_proxies = [p for p in self.settings.proxies if p.enabled]
        available_proxies.sort(key=lambda x: x.priority)
        
        # Test proxies if health check is due
        current_time = time.time()
        if (current_time - self._last_health_check) > self.settings.health_check_interval:
            self._perform_health_checks()
            self._last_health_check = current_time
        
        # Select first healthy proxy
        for proxy in available_proxies:
            if proxy.name in self.proxy_health:
                is_healthy, _ = self.proxy_health[proxy.name]
                if is_healthy:
                    self.active_proxy = proxy
                    logger.info(f"Selected proxy: {proxy.name} ({proxy.host}:{proxy.port})")
                    return proxy
        
        # If no healthy proxy found, try the first available one
        if available_proxies:
            self.active_proxy = available_proxies[0]
            logger.warning(f"No healthy proxy found, using: {self.active_proxy.name}")
            return self.active_proxy
            
        return None

    def _perform_health_checks(self):
        """Perform health checks on all configured proxies."""
        logger.info("Performing proxy health checks...")
        
        for proxy in self.settings.proxies:
            if not proxy.enabled:
                continue
                
            success, latency, error = proxy.test_connection(self.settings.test_timeout)
            self.proxy_health[proxy.name] = (success, time.time())
            
            if success:
                logger.info(f"Proxy {proxy.name} is healthy (latency: {latency:.2f}ms)")
            else:
                logger.warning(f"Proxy {proxy.name} is unhealthy: {error}")

    def create_session(self, protocol: str = "https") -> requests.Session:
        """
        Create a requests session configured with proxy settings.
        
        Args:
            protocol: The protocol to optimize for ('http' or 'https')
            
        Returns:
            Configured requests.Session with proxy and retry logic
        """
        session = requests.Session()
        
        if not self.settings.enabled or not self.active_proxy:
            logger.info("Proxy not enabled or no active proxy, using direct connection")
            return session
        
        # Configure proxy
        session.proxies.update(self.active_proxy.proxy_dict)
        
        # Configure authentication if needed
        if self.active_proxy.username and self.active_proxy.password:
            session.auth = HTTPProxyAuth(self.active_proxy.username, self.active_proxy.password)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.settings.max_retries,
            backoff_factor=self.settings.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set timeout
        session.timeout = REQUESTS_TIMEOUT_SEC
        
        logger.info(f"Created proxy session using {self.active_proxy.name}")
        return session

    def create_tidal_session(self) -> requests.Session:
        """
        Create a specialized session for TIDAL API requests.
        
        This ensures all TIDAL communication is routed through the proxy
        for complete location masking.
        """
        session = self.create_session("https")
        
        # Add TIDAL-specific headers
        session.headers.update({
            'User-Agent': 'TIDAL-Desktop/2.34.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        logger.info("Created TIDAL-specific proxy session for location masking")
        return session

    def test_proxy_connectivity(self) -> Dict[str, Tuple[bool, float, Optional[str]]]:
        """
        Test connectivity for all configured proxies.
        
        Returns:
            Dictionary mapping proxy names to (success, latency, error) tuples
        """
        results = {}
        
        for proxy in self.settings.proxies:
            if proxy.enabled:
                success, latency, error = proxy.test_connection(self.settings.test_timeout)
                results[proxy.name] = (success, latency, error)
        
        return results

    def get_proxy_status(self) -> Dict[str, Any]:
        """
        Get current proxy status and information.
        
        Returns:
            Dictionary containing proxy status, configuration, and location info
        """
        if not self.settings.enabled:
            return {"enabled": False, "status": "Proxy disabled"}
        
        if not self.settings.proxies:
            return {"enabled": False, "status": "No proxies configured"}
        
        if not self.active_proxy:
            return {"enabled": True, "status": "No active proxy", "error": "No healthy proxy available"}
        
        # Get current IP and location info
        success, location_info = self.validate_location_masking()
        
        return {
            "enabled": True,
            "status": "Active",
            "proxy_name": self.active_proxy.name,
            "proxy_host": self.active_proxy.host,
            "proxy_port": self.active_proxy.port,
            "proxy_type": self.active_proxy.proxy_type,
            "location_masking": success,
            "location_info": location_info,
            "total_proxies": len(self.settings.proxies),
            "enabled_proxies": len([p for p in self.settings.proxies if p.enabled])
        }

    def get_current_ip(self) -> Optional[str]:
        """
        Get the current external IP address as seen through the proxy.
        
        Returns:
            External IP address or None if unable to determine
        """
        if not self.settings.enabled or not self.active_proxy:
            return None
            
        try:
            session = self.create_session()
            response = session.get("https://api.ipify.org?format=json", timeout=10)
            response.raise_for_status()
            return response.json().get("ip")
        except Exception as e:
            logger.error(f"Failed to get current IP: {str(e)}")
            return None

    def validate_location_masking(self) -> Tuple[bool, Dict[str, str]]:
        """
        Validate that location masking is working correctly.
        
        Returns:
            Tuple of (success, location_info)
        """
        if not self.settings.enabled or not self.active_proxy:
            return False, {"error": "Proxy not enabled or configured"}
        
        try:
            session = self.create_session()
            
            # Get IP through proxy
            ip_response = session.get("https://httpbin.org/ip", timeout=10)
            ip_response.raise_for_status()
            ip_info = ip_response.json()
            proxy_ip = ip_info.get("origin")
            
            # Get direct IP for comparison
            import requests
            direct_response = requests.get("https://httpbin.org/ip", timeout=10)
            direct_response.raise_for_status()
            direct_ip = direct_response.json().get("origin")
            
            # Basic validation - IPs should be different
            if proxy_ip == direct_ip:
                return False, {"error": "Proxy not working - same IP detected"}
            
            # Try to get location info (with fallback if rate limited)
            location_info = {
                "ip": proxy_ip,
                "direct_ip": direct_ip,
                "proxy_name": self.active_proxy.name,
                "proxy_working": True
            }
            
            # Try multiple geolocation services
            geo_services = [
                f"https://ipapi.co/{proxy_ip}/json/",
                f"http://ip-api.com/json/{proxy_ip}",
                f"https://freegeoip.app/json/{proxy_ip}"
            ]
            
            for service_url in geo_services:
                try:
                    geo_response = session.get(service_url, timeout=10)
                    if geo_response.status_code == 200:
                        geo_info = geo_response.json()
                        
                        # Handle different API response formats
                        if "country_name" in geo_info:  # ipapi.co format
                            location_info.update({
                                "country": geo_info.get("country_name"),
                                "city": geo_info.get("city"),
                                "region": geo_info.get("region"),
                                "isp": geo_info.get("org")
                            })
                        elif "country" in geo_info:  # ip-api.com format
                            location_info.update({
                                "country": geo_info.get("country"),
                                "city": geo_info.get("city"),
                                "region": geo_info.get("regionName"),
                                "isp": geo_info.get("isp")
                            })
                        elif "country_name" in geo_info:  # freegeoip.app format
                            location_info.update({
                                "country": geo_info.get("country_name"),
                                "city": geo_info.get("city"),
                                "region": geo_info.get("region_name"),
                                "isp": "Unknown"
                            })
                        
                        break  # Success, stop trying other services
                        
                except Exception as e:
                    logger.debug(f"Geolocation service {service_url} failed: {str(e)}")
                    continue
            
            # If no geolocation worked, still return success if IPs are different
            if "country" not in location_info:
                location_info.update({
                    "country": "Unknown (geolocation services unavailable)",
                    "city": "Unknown",
                    "region": "Unknown",
                    "isp": "Unknown"
                })
            
            logger.info(f"Location masking validation successful: {location_info}")
            return True, location_info
            
        except Exception as e:
            error_info = {"error": f"Location validation failed: {str(e)}"}
            logger.error(error_info["error"])
            return False, error_info

    def add_proxy(self, proxy_config: ProxyConfig):
        """Add a new proxy configuration."""
        self.settings.proxies.append(proxy_config)
        if self.settings.enabled and not self.active_proxy:
            self._select_best_proxy()

    def remove_proxy(self, proxy_name: str) -> bool:
        """Remove a proxy configuration by name."""
        for i, proxy in enumerate(self.settings.proxies):
            if proxy.name == proxy_name:
                del self.settings.proxies[i]
                if self.active_proxy and self.active_proxy.name == proxy_name:
                    self.active_proxy = None
                    self._select_best_proxy()
                return True
        return False

    def enable_proxy(self, proxy_name: str) -> bool:
        """Enable a specific proxy."""
        for proxy in self.settings.proxies:
            if proxy.name == proxy_name:
                proxy.enabled = True
                if self.settings.enabled:
                    self._select_best_proxy()
                return True
        return False

    def disable_proxy(self, proxy_name: str) -> bool:
        """Disable a specific proxy."""
        for proxy in self.settings.proxies:
            if proxy.name == proxy_name:
                proxy.enabled = False
                if self.active_proxy and self.active_proxy.name == proxy_name:
                    self.active_proxy = None
                    self._select_best_proxy()
                return True
        return False
