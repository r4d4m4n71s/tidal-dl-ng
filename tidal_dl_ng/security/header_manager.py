"""
HTTP header management and randomization.

This module provides dynamic header generation and User-Agent rotation
to make requests appear to come from different clients and devices.
"""

import random
import requests
from typing import Dict, List, Optional


class HeaderManager:
    """Manages HTTP headers and User-Agent rotation for request obfuscation."""
    
    def __init__(self):
        """Initialize the header manager."""
        self.user_agents = [
            # Desktop browsers - Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Desktop browsers - Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
            
            # Desktop browsers - Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            
            # Desktop browsers - Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # Mobile apps - TIDAL official
            "TIDAL/2.38.0 (iPhone; iOS 17.2.1; Scale/3.00)",
            "TIDAL/2.38.0 (Android 14; SM-G998B)",
            "TIDAL/2.76.0 (Windows 11)",
            "TIDAL/2.76.0 (macOS 14.2)",
            
            # Mobile browsers
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ]
        
        self.accept_languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,es;q=0.8",
            "en-US,en;q=0.9,fr;q=0.8",
            "en-US,en;q=0.9,de;q=0.8",
            "es-ES,es;q=0.9,en;q=0.8",
            "fr-FR,fr;q=0.9,en;q=0.8",
            "de-DE,de;q=0.9,en;q=0.8",
            "pt-BR,pt;q=0.9,en;q=0.8",
        ]
        
        self.accept_encodings = [
            "gzip, deflate, br",
            "gzip, deflate",
            "gzip, deflate, br, zstd",
        ]
        
        self.connection_types = [
            "keep-alive",
            "close",
        ]
        
        self.cache_controls = [
            "no-cache",
            "max-age=0",
            "no-cache, no-store",
            "private, max-age=0",
        ]
        
    def get_random_user_agent(self) -> str:
        """Get a random User-Agent string."""
        return random.choice(self.user_agents)
        
    def get_tidal_user_agent(self) -> str:
        """Get a TIDAL-specific User-Agent string."""
        tidal_agents = [ua for ua in self.user_agents if "TIDAL" in ua]
        return random.choice(tidal_agents) if tidal_agents else self.get_random_user_agent()
        
    def get_browser_user_agent(self) -> str:
        """Get a browser User-Agent string."""
        browser_agents = [ua for ua in self.user_agents if "TIDAL" not in ua]
        return random.choice(browser_agents)
        
    def get_random_headers(self, include_tidal_specific: bool = False) -> Dict[str, str]:
        """
        Generate randomized but realistic HTTP headers.
        
        Args:
            include_tidal_specific: Whether to include TIDAL-specific headers
            
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'User-Agent': self.get_tidal_user_agent() if include_tidal_specific else self.get_random_user_agent(),
            'Accept-Language': random.choice(self.accept_languages),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': random.choice(self.accept_encodings),
            'Cache-Control': random.choice(self.cache_controls),
            'Connection': random.choice(self.connection_types),
        }
        
        # Randomly add optional headers
        if random.random() < 0.7:
            headers['DNT'] = '1'
            
        if random.random() < 0.5:
            headers['Upgrade-Insecure-Requests'] = '1'
            
        if random.random() < 0.3:
            headers['Sec-Fetch-Dest'] = random.choice(['empty', 'document', 'audio'])
            
        if random.random() < 0.4:
            headers['Sec-Fetch-Mode'] = random.choice(['cors', 'navigate', 'no-cors'])
            
        if random.random() < 0.4:
            headers['Sec-Fetch-Site'] = random.choice(['same-origin', 'cross-site', 'none'])
            
        # Add random referer occasionally
        if random.random() < 0.2:
            referers = [
                'https://listen.tidal.com/',
                'https://tidal.com/',
                'https://www.google.com/',
                'https://duckduckgo.com/',
            ]
            headers['Referer'] = random.choice(referers)
            
        # Add TIDAL-specific headers if requested
        if include_tidal_specific:
            if random.random() < 0.8:
                headers['X-Tidal-Token'] = self._generate_mock_token()
                
            if random.random() < 0.6:
                headers['Origin'] = 'https://listen.tidal.com'
                
        return headers
        
    def _generate_mock_token(self) -> str:
        """Generate a mock token for TIDAL-specific headers."""
        # Generate a realistic-looking token
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(32))
        
    def get_session_with_headers(self, proxy_list: Optional[List[str]] = None) -> requests.Session:
        """
        Create a requests session with randomized headers and optional proxy.
        
        Args:
            proxy_list: Optional list of proxy URLs
            
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Set random proxy if list provided
        if proxy_list:
            proxy = random.choice(proxy_list)
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
            
        # Apply random headers
        session.headers.update(self.get_random_headers())
        
        return session
        
    def rotate_headers(self, session: requests.Session) -> None:
        """
        Rotate headers on an existing session.
        
        Args:
            session: Requests session to update
        """
        # Clear existing headers and set new ones
        session.headers.clear()
        session.headers.update(self.get_random_headers())
        
    def get_download_headers(self) -> Dict[str, str]:
        """Get headers optimized for download requests."""
        headers = self.get_random_headers()
        
        # Override some headers for downloads
        headers['Accept'] = '*/*'
        headers['Sec-Fetch-Dest'] = 'audio'
        headers['Sec-Fetch-Mode'] = 'cors'
        
        # Remove cache control for downloads
        if 'Cache-Control' in headers:
            del headers['Cache-Control']
            
        return headers
        
    def get_api_headers(self) -> Dict[str, str]:
        """Get headers optimized for API requests."""
        headers = self.get_random_headers(include_tidal_specific=True)
        
        # API-specific headers
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        
        return headers
        
    def add_auth_headers(self, headers: Dict[str, str], token: str) -> Dict[str, str]:
        """
        Add authentication headers to existing headers.
        
        Args:
            headers: Existing headers
            token: Authentication token
            
        Returns:
            Headers with authentication added
        """
        auth_headers = headers.copy()
        auth_headers['Authorization'] = f'Bearer {token}'
        return auth_headers
        
    def simulate_browser_headers(self, url: str) -> Dict[str, str]:
        """
        Generate headers that simulate a browser visiting a specific URL.
        
        Args:
            url: URL being visited
            
        Returns:
            Browser-like headers
        """
        headers = {
            'User-Agent': self.get_browser_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(self.accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Add referer for non-initial requests
        if random.random() < 0.3:
            headers['Referer'] = 'https://www.google.com/'
            
        return headers
        
    def get_mobile_headers(self) -> Dict[str, str]:
        """Get headers that simulate a mobile device."""
        mobile_agents = [ua for ua in self.user_agents if any(mobile in ua for mobile in ['iPhone', 'Android', 'Mobile'])]
        
        headers = self.get_random_headers()
        headers['User-Agent'] = random.choice(mobile_agents)
        
        # Mobile-specific headers
        if 'iPhone' in headers['User-Agent']:
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        else:  # Android
            headers['X-Requested-With'] = 'com.aspiro.tidal'
            
        return headers
        
    def vary_header_order(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Randomize the order of headers (some servers may log header order).
        
        Args:
            headers: Headers to reorder
            
        Returns:
            Headers in random order
        """
        items = list(headers.items())
        random.shuffle(items)
        return dict(items)
