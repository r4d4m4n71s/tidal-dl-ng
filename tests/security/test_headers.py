"""
Test header randomization and request obfuscation.
"""
import pytest
from collections import Counter
from unittest.mock import patch, MagicMock

from tidal_dl_ng.security.header_manager import HeaderManager
from tidal_dl_ng import api


class TestHeaderSecurity:
    """Test suite for header security features."""
    
    def setup_method(self):
        """Set up test environment."""
        self.header_manager = HeaderManager()
    
    def test_user_agent_diversity(self):
        """Test that multiple User-Agent strings are available."""
        assert len(self.header_manager.user_agents) >= 10
        
        # Check for different types
        desktop_count = sum(1 for ua in self.header_manager.user_agents if 'Windows' in ua or 'Mac' in ua or 'Linux' in ua)
        mobile_count = sum(1 for ua in self.header_manager.user_agents if 'Mobile' in ua or 'Android' in ua or 'iPhone' in ua)
        tidal_count = sum(1 for ua in self.header_manager.user_agents if 'TIDAL' in ua)
        
        assert desktop_count > 0, "Should have desktop User-Agents"
        assert mobile_count > 0, "Should have mobile User-Agents"
        assert tidal_count > 0, "Should have TIDAL-specific User-Agents"
    
    def test_user_agent_randomization(self):
        """Test that User-Agent selection is random."""
        user_agents = []
        for _ in range(50):
            ua = self.header_manager.get_random_user_agent()
            user_agents.append(ua)
        
        # Should have variety
        unique_uas = set(user_agents)
        assert len(unique_uas) > 1, "Should return different User-Agents"
        
        # Distribution shouldn't be too skewed
        ua_counts = Counter(user_agents)
        max_count = max(ua_counts.values())
        assert max_count < 40, "User-Agent selection should be reasonably random"
    
    def test_tidal_specific_user_agents(self):
        """Test TIDAL-specific User-Agent selection."""
        for _ in range(10):
            ua = self.header_manager.get_tidal_user_agent()
            assert 'TIDAL' in ua, "Should return TIDAL User-Agents"
    
    def test_browser_user_agents(self):
        """Test browser User-Agent selection."""
        for _ in range(10):
            ua = self.header_manager.get_browser_user_agent()
            assert 'TIDAL' not in ua, "Should not return TIDAL User-Agents"
            assert any(browser in ua for browser in ['Chrome', 'Firefox', 'Safari', 'Edge'])
    
    def test_header_randomization(self):
        """Test that headers are randomized properly."""
        headers_list = []
        for _ in range(20):
            headers = self.header_manager.get_random_headers()
            headers_list.append(headers)
        
        # Check required headers
        for headers in headers_list:
            assert 'User-Agent' in headers
            assert 'Accept-Language' in headers
            assert 'Accept' in headers
            assert 'Accept-Encoding' in headers
        
        # Check for variety in optional headers
        dnt_count = sum(1 for h in headers_list if 'DNT' in h)
        # DNT has 30% chance, so in 20 attempts we expect 3-13 (with some margin)
        assert 2 <= dnt_count <= 18, "DNT header should appear randomly"
        
        # Check language variety
        languages = [h['Accept-Language'] for h in headers_list]
        unique_languages = set(languages)
        assert len(unique_languages) > 1, "Should have language variety"
    
    def test_tidal_specific_headers(self):
        """Test TIDAL-specific header generation."""
        headers_list = []
        for _ in range(20):
            headers = self.header_manager.get_random_headers(include_tidal_specific=True)
            headers_list.append(headers)
        
        # Should include TIDAL-specific headers sometimes
        token_count = sum(1 for h in headers_list if 'X-Tidal-Token' in h)
        assert token_count > 0, "Should include TIDAL tokens"
        
        origin_count = sum(1 for h in headers_list if 'Origin' in h)
        assert origin_count > 0, "Should include Origin header"
    
    def test_download_headers(self):
        """Test headers optimized for downloads."""
        headers = self.header_manager.get_download_headers()
        
        assert headers['Accept'] == '*/*'
        assert headers['Sec-Fetch-Dest'] == 'audio'
        assert headers['Sec-Fetch-Mode'] == 'cors'
        assert 'Cache-Control' not in headers
    
    def test_api_headers(self):
        """Test headers optimized for API requests."""
        headers = self.header_manager.get_api_headers()
        
        assert headers['Content-Type'] == 'application/json'
        assert headers['Accept'] == 'application/json'
        assert 'User-Agent' in headers
    
    def test_session_creation_with_headers(self):
        """Test session creation with randomized headers."""
        session = self.header_manager.get_session_with_headers()
        
        assert len(session.headers) > 0
        assert 'User-Agent' in session.headers
        
        # Test with proxy
        proxy_list = ['http://proxy1.com', 'http://proxy2.com']
        session_with_proxy = self.header_manager.get_session_with_headers(proxy_list)
        assert 'http' in session_with_proxy.proxies
        assert 'https' in session_with_proxy.proxies
    
    def test_header_rotation(self):
        """Test header rotation on existing session."""
        import requests
        session = requests.Session()
        
        # Set initial headers
        initial_ua = "Initial User-Agent"
        session.headers['User-Agent'] = initial_ua
        
        # Rotate headers
        self.header_manager.rotate_headers(session)
        
        # Headers should be changed
        assert session.headers['User-Agent'] != initial_ua
        assert len(session.headers) > 1
    
    def test_auth_header_addition(self):
        """Test adding authentication headers."""
        base_headers = {'User-Agent': 'Test'}
        token = 'test_token_12345'
        
        auth_headers = self.header_manager.add_auth_headers(base_headers, token)
        
        assert 'Authorization' in auth_headers
        assert auth_headers['Authorization'] == f'Bearer {token}'
        assert 'User-Agent' in auth_headers  # Original headers preserved
    
    def test_browser_simulation_headers(self):
        """Test browser simulation headers."""
        url = 'https://listen.tidal.com/browse'
        headers = self.header_manager.simulate_browser_headers(url)
        
        # Should look like a browser
        assert 'text/html' in headers['Accept']
        assert headers['Upgrade-Insecure-Requests'] == '1'
        assert headers['Sec-Fetch-Dest'] == 'document'
        assert headers['Sec-Fetch-Mode'] == 'navigate'
        
        # Should not have TIDAL in User-Agent
        assert 'TIDAL' not in headers['User-Agent']
    
    def test_mobile_headers(self):
        """Test mobile device headers."""
        headers = self.header_manager.get_mobile_headers()
        
        # Should have mobile User-Agent
        ua = headers['User-Agent']
        assert any(mobile in ua for mobile in ['iPhone', 'Android', 'Mobile'])
        
        # Test multiple times for variety
        mobile_types = set()
        for _ in range(10):
            h = self.header_manager.get_mobile_headers()
            if 'iPhone' in h['User-Agent']:
                mobile_types.add('iOS')
            elif 'Android' in h['User-Agent']:
                mobile_types.add('Android')
        
        assert len(mobile_types) > 1, "Should have both iOS and Android agents"
    
    def test_header_order_variation(self):
        """Test that header order can be varied."""
        headers = {
            'User-Agent': 'Test',
            'Accept': 'application/json',
            'Accept-Language': 'en-US',
            'Connection': 'keep-alive'
        }
        
        # Get different orderings
        orders = []
        for _ in range(10):
            varied = self.header_manager.vary_header_order(headers)
            orders.append(list(varied.keys()))
        
        # Should have different orders
        unique_orders = [tuple(order) for order in orders]
        assert len(set(unique_orders)) > 1, "Header order should vary"


class TestHeaderSecurityIntegration:
    """Integration tests for header security with API module."""
    
    def test_api_uses_secure_headers(self):
        """Test that API module uses secure headers."""
        headers = api.get_secure_headers()
        
        # Should have randomized headers
        assert 'User-Agent' in headers
        assert 'Accept-Language' in headers
        
        # Get multiple times to check randomization
        headers_list = [api.get_secure_headers() for _ in range(10)]
        
        # Check for variety
        user_agents = [h['User-Agent'] for h in headers_list]
        unique_uas = set(user_agents)
        assert len(unique_uas) > 1, "API should use varied User-Agents"
    
    def test_session_setup_integration(self):
        """Test secure session setup through API."""
        session = api.setup_secure_session()
        
        # Should have headers configured
        assert 'User-Agent' in session.headers
        assert session.headers['User-Agent'] != ''
        
        # Headers should be from the pool
        header_manager = HeaderManager()
        assert any(session.headers['User-Agent'] == ua 
                  for ua in header_manager.user_agents)
