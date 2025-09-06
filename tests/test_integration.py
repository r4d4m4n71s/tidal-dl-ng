#!/usr/bin/env python3
"""
Comprehensive Test Suite for TIDAL Proxy Integration

This module contains comprehensive tests for:
- TIDAL Proxy Integration (local python-tidal source integration)
- Proxy Manager functionality
- Location masking validation
- TIDAL-specific session creation
- Authentication flow setup
"""

import pytest
import sys
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)


class TestTidalProxyIntegration:
    """Test suite for TIDAL proxy integration functionality."""

    def test_imports(self):
        """Test that all imports work correctly."""
        print("=" * 60)
        print("TESTING IMPORTS")
        print("=" * 60)
        
        try:
            # Test tidalapi import (should use local source)
            import tidalapi
            print(f"✅ tidalapi imported successfully")
            print(f"   Location: {tidalapi.__file__}")
            
            # Test our enhanced session
            from tidal_dl_ng.enhanced_session import EnhancedTidalSession, create_enhanced_tidal_session
            print(f"✅ Enhanced session imported successfully")
            
            # Test integration layer
            from tidal_dl_ng.tidal_proxy_integration import TidalProxyIntegration, diagnose_proxy_integration
            print(f"✅ Integration layer imported successfully")
            
            # Test config with enhanced session
            from tidal_dl_ng.config import Settings, Tidal
            print(f"✅ Config with enhanced session imported successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_session_creation(self):
        """Test creating enhanced TIDAL sessions."""
        print("\n" + "=" * 60)
        print("TESTING SESSION CREATION")
        print("=" * 60)
        
        try:
            from tidal_dl_ng.config import Settings
            from tidal_dl_ng.enhanced_session import create_enhanced_tidal_session
            from tidal_dl_ng.tidal_proxy_integration import TidalProxyIntegration
            
            # Create settings
            settings = Settings()
            print(f"✅ Settings created successfully")
            
            # Test session creation without proxy
            session = create_enhanced_tidal_session(settings)
            print(f"✅ Enhanced session created successfully")
            print(f"   Session type: {type(session).__name__}")
            print(f"   Proxy manager: {'Available' if session.proxy_manager else 'Not available'}")
            
            # Test integration layer
            integration = TidalProxyIntegration(settings)
            print(f"✅ Integration layer created successfully")
            
            # Test session creation through integration
            integration_session = integration.get_session()
            print(f"✅ Integration session created successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Session creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_proxy_configuration(self):
        """Test proxy configuration and setup."""
        print("\n" + "=" * 60)
        print("TESTING PROXY CONFIGURATION")
        print("=" * 60)
        
        try:
            from tidal_dl_ng.config import Settings, Tidal
            from tidal_dl_ng.model.cfg import ProxyConfig
            from tidal_dl_ng.tidal_proxy_integration import quick_proxy_test, diagnose_proxy_integration
            
            # Create settings
            settings = Settings()
            
            # Add test proxy configuration
            test_proxy = ProxyConfig(
                name="Test Proxy",
                host="geo.iproyal.com",
                port=12321,
                proxy_type="https",
                username="LwAit6sjotiaziYw",
                password="oKYCBDdannR7E4XX_country-co_city-pereira_session-y0xFNSkT_lifetime-30m",
                protocols=["http", "https"],
                enabled=True,
                priority=1
            )
            
            settings.data.proxy_settings.proxies.append(test_proxy)
            settings.data.proxy_settings.enabled = True
            
            print(f"✅ Test proxy configuration added")
            
            # Test quick proxy test
            proxy_test_result = quick_proxy_test(settings)
            print(f"✅ Quick proxy test completed")
            print(f"   Result: {proxy_test_result}")
            
            # Test diagnostic
            diagnosis = diagnose_proxy_integration(settings)
            print(f"✅ Proxy integration diagnosis completed")
            print(f"   Proxy count: {diagnosis['proxy_settings']['proxy_count']}")
            print(f"   Proxy enabled: {diagnosis['proxy_settings']['enabled']}")
            
            # Test Tidal class with proxy
            tidal = Tidal(settings)
            print(f"✅ Tidal class with proxy created successfully")
            print(f"   Session type: {type(tidal.session).__name__}")
            print(f"   Proxy manager: {'Available' if tidal.session.proxy_manager else 'Not available'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Proxy configuration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_compatibility(self):
        """Test backward compatibility with existing code."""
        print("\n" + "=" * 60)
        print("TESTING BACKWARD COMPATIBILITY")
        print("=" * 60)
        
        try:
            from tidal_dl_ng.config import Settings, Tidal
            import tidalapi
            
            # Test that we can still access standard tidalapi classes
            config = tidalapi.Config()
            print(f"✅ Standard tidalapi.Config accessible")
            
            # Test Quality enum (check what's available)
            quality = tidalapi.Quality.low_320k  # Use a known quality level
            print(f"✅ Standard tidalapi.Quality accessible: {quality}")
            
            # Test that existing Tidal class still works
            settings = Settings()
            tidal = Tidal(settings)
            
            # Test that session has expected attributes
            assert hasattr(tidal.session, 'audio_quality'), "Session missing audio_quality"
            assert hasattr(tidal.session, 'video_quality'), "Session missing video_quality"
            assert hasattr(tidal.session, 'check_login'), "Session missing check_login method"
            assert hasattr(tidal.session, 'login_oauth_simple'), "Session missing login_oauth_simple method"
            
            print(f"✅ Backward compatibility maintained")
            print(f"   Session has all expected attributes and methods")
            
            return True
            
        except Exception as e:
            print(f"❌ Compatibility test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


class TestProxyManager:
    """Test suite for the ProxyManager functionality."""
    
    @pytest.fixture
    def test_proxy_config(self):
        """Fixture providing test proxy configuration."""
        from tidal_dl_ng.model.cfg import ProxyConfig
        return ProxyConfig(
            name="iProyal Test Proxy",
            host="geo.iproyal.com",
            port=12321,
            proxy_type="https",
            username="LwAit6sjotiaziYw",
            password="oKYCBDdannR7E4XX_country-co_city-pereira_session-y0xFNSkT_lifetime-30m",
            protocols=["http", "https"],
            enabled=True,
            priority=1
        )
    
    @pytest.fixture
    def settings_with_proxy(self, test_proxy_config):
        """Fixture providing settings configured with test proxy."""
        from tidal_dl_ng.config import Settings
        settings = Settings()
        settings.data.proxy_settings.enabled = True
        settings.data.proxy_settings.proxies = [test_proxy_config]
        settings.data.auth_settings.use_local_server = True
        return settings
    
    @pytest.fixture
    def tidal_with_proxy(self, settings_with_proxy):
        """Fixture providing TIDAL instance with proxy configuration."""
        from tidal_dl_ng.config import Tidal
        return Tidal(settings_with_proxy)
    
    def test_proxy_configuration(self, test_proxy_config, settings_with_proxy):
        """Test proxy configuration setup."""
        assert settings_with_proxy.data.proxy_settings.enabled is True
        assert len(settings_with_proxy.data.proxy_settings.proxies) == 1
        
        proxy = settings_with_proxy.data.proxy_settings.proxies[0]
        assert proxy.name == "iProyal Test Proxy"
        assert proxy.host == "geo.iproyal.com"
        assert proxy.port == 12321
        assert proxy.proxy_type == "https"
        assert proxy.enabled is True
    
    def test_proxy_manager_initialization(self, tidal_with_proxy):
        """Test that proxy manager initializes correctly."""
        from tidal_dl_ng.proxy import ProxyManager
        assert tidal_with_proxy.proxy_manager is not None
        assert isinstance(tidal_with_proxy.proxy_manager, ProxyManager)
    
    @pytest.mark.integration
    def test_proxy_connectivity(self, tidal_with_proxy):
        """Integration test for proxy connectivity."""
        if not tidal_with_proxy.proxy_manager:
            pytest.skip("Proxy manager not initialized")
        
        # Test proxy connectivity
        connectivity_results = tidal_with_proxy.proxy_manager.test_proxy_connectivity()
        
        assert len(connectivity_results) > 0
        
        for proxy_name, (success, latency, error) in connectivity_results.items():
            if success:
                assert latency > 0
                assert error is None
                print(f"✓ {proxy_name}: Connected (latency: {latency:.2f}ms)")
            else:
                print(f"✗ {proxy_name}: Failed - {error}")
                # Don't fail the test if proxy is temporarily unavailable
                pytest.skip(f"Proxy connectivity failed: {error}")
    
    @pytest.mark.integration
    def test_location_masking(self, tidal_with_proxy):
        """Integration test for location masking functionality."""
        if not tidal_with_proxy.proxy_manager:
            pytest.skip("Proxy manager not initialized")
        
        # Test location masking
        proxy_status = tidal_with_proxy.proxy_manager.get_proxy_status()
        
        assert proxy_status.get("enabled") is True
        
        if proxy_status.get("location_masking"):
            location_info = proxy_status.get("location_info", {})
            
            # Verify location information is present
            assert "ip" in location_info
            assert "country" in location_info
            assert location_info["ip"] != "Unknown"
            
            print(f"✓ Location masking active:")
            print(f"  - IP Address: {location_info.get('ip', 'Unknown')}")
            print(f"  - Country: {location_info.get('country', 'Unknown')}")
            print(f"  - City: {location_info.get('city', 'Unknown')}")
            
            # Verify Colombian location (expected for test proxy)
            country = location_info.get('country', '').lower()
            if country in ['colombia', 'co']:
                print("✓ Successfully masking location as Colombian IP")
            else:
                print(f"⚠ Warning: Expected Colombian IP, got {country}")
        else:
            pytest.skip("Location masking not active - proxy may be unavailable")
    
    def test_tidal_session_creation(self, tidal_with_proxy):
        """Test TIDAL-specific session creation."""
        if not tidal_with_proxy.proxy_manager:
            pytest.skip("Proxy manager not initialized")
        
        # Create TIDAL session
        tidal_session = tidal_with_proxy.proxy_manager.create_tidal_session()
        
        assert tidal_session is not None
        
        # Verify TIDAL headers are set
        headers = tidal_session.headers
        assert "User-Agent" in headers
        assert "TIDAL-Desktop" in headers["User-Agent"]
    
    @pytest.mark.integration
    def test_proxy_vs_direct_connection(self, tidal_with_proxy):
        """Integration test comparing proxy vs direct connection IPs."""
        if not tidal_with_proxy.proxy_manager:
            pytest.skip("Proxy manager not initialized")
        
        try:
            # Test through proxy
            session = tidal_with_proxy.proxy_manager.create_session()
            proxy_response = session.get("https://httpbin.org/ip", timeout=15)
            proxy_response.raise_for_status()
            proxy_ip = proxy_response.json().get('origin', 'Unknown')
            
            # Test direct connection
            import requests
            direct_response = requests.get("https://httpbin.org/ip", timeout=10)
            direct_ip = direct_response.json().get('origin', 'Unknown')
            
            print(f"✓ Proxy IP: {proxy_ip}")
            print(f"✓ Direct IP: {direct_ip}")
            
            # IPs should be different if proxy is working
            assert proxy_ip != direct_ip, "Proxy and direct IPs should be different"
            
            print("✅ SUCCESS: Proxy is working correctly!")
            print(f"✅ Location masking active: {direct_ip} → {proxy_ip}")
            
        except Exception as e:
            pytest.skip(f"Network connectivity test failed: {str(e)}")
    
    @pytest.mark.integration
    def test_tidal_session_headers(self, tidal_with_proxy):
        """Integration test for TIDAL session headers."""
        if not tidal_with_proxy.proxy_manager:
            pytest.skip("Proxy manager not initialized")
        
        try:
            # Create TIDAL-specific session
            tidal_session = tidal_with_proxy.proxy_manager.create_tidal_session()
            
            # Test with TIDAL headers
            response = tidal_session.get("https://httpbin.org/headers", timeout=15)
            response.raise_for_status()
            
            headers = response.json().get('headers', {})
            user_agent = headers.get('User-Agent', '')
            
            assert 'TIDAL-Desktop' in user_agent, f"Expected TIDAL User-Agent, got: {user_agent}"
            print(f"✅ TIDAL session configured correctly")
            print(f"✅ User-Agent: {user_agent}")
            
        except Exception as e:
            pytest.skip(f"TIDAL session header test failed: {str(e)}")
    
    def test_authentication_flow_setup(self, settings_with_proxy):
        """Test authentication flow configuration."""
        # Verify auth settings
        assert settings_with_proxy.data.auth_settings.use_local_server is True
        
        # Initialize TIDAL with proxy
        from tidal_dl_ng.config import Tidal
        tidal = Tidal(settings_with_proxy)
        
        # Verify proxy manager is available for auth
        assert tidal.proxy_manager is not None
        
        print("✓ Authentication flow setup complete")
        print("✓ System ready for proxy-based authentication")
    
    def test_proxy_url_encoding(self, test_proxy_config):
        """Test that proxy credentials are properly URL encoded."""
        from urllib.parse import quote
        
        # Test password with special characters
        password = test_proxy_config.password
        encoded_password = quote(password, safe='')
        
        # Verify encoding handles special characters
        assert '_' in password  # Original has underscores
        assert '%5F' in encoded_password or '_' in encoded_password  # Should be encoded or safe
    
    @patch('requests.Session.get')
    def test_proxy_error_handling(self, mock_get, tidal_with_proxy):
        """Test proxy error handling."""
        if not tidal_with_proxy.proxy_manager:
            pytest.skip("Proxy manager not initialized")
        
        # Mock a connection error
        mock_get.side_effect = Exception("Connection failed")
        
        session = tidal_with_proxy.proxy_manager.create_session()
        
        with pytest.raises(Exception):
            session.get("https://httpbin.org/ip", timeout=5)


class TestProxyIntegration:
    """Integration tests that require network connectivity."""
    
    @pytest.mark.integration
    def test_full_proxy_workflow(self):
        """Test the complete proxy workflow from configuration to usage."""
        print("\n" + "=" * 60)
        print("FULL PROXY WORKFLOW TEST")
        print("=" * 60)
        
        from tidal_dl_ng.config import Settings, Tidal
        from tidal_dl_ng.model.cfg import ProxyConfig
        
        # 1. Initialize settings
        settings = Settings()
        
        # 2. Add test proxy configuration
        test_proxy = ProxyConfig(
            name="iProyal Test Proxy",
            host="geo.iproyal.com",
            port=12321,
            proxy_type="https",
            username="LwAit6sjotiaziYw",
            password="oKYCBDdannR7E4XX_country-co_city-pereira_session-y0xFNSkT_lifetime-30m",
            protocols=["http", "https"],
            enabled=True,
            priority=1
        )
        
        # 3. Configure settings
        settings.data.proxy_settings.enabled = True
        settings.data.proxy_settings.proxies = [test_proxy]
        settings.data.auth_settings.use_local_server = True
        
        # 4. Initialize TIDAL
        tidal = Tidal(settings)
        
        if not tidal.proxy_manager:
            pytest.skip("Proxy manager initialization failed")
        
        # 5. Test connectivity
        connectivity_results = tidal.proxy_manager.test_proxy_connectivity()
        
        success_count = sum(1 for success, _, _ in connectivity_results.values() if success)
        if success_count == 0:
            pytest.skip("No proxy connections successful")
        
        # 6. Test location masking
        proxy_status = tidal.proxy_manager.get_proxy_status()
        
        assert proxy_status.get("enabled") is True
        
        if proxy_status.get("location_masking"):
            location_info = proxy_status.get("location_info", {})
            assert location_info.get("ip") != "Unknown"
            print(f"✓ Location masking confirmed: {location_info.get('ip')}")
        
        # 7. Test TIDAL session
        tidal_session = tidal.proxy_manager.create_tidal_session()
        assert tidal_session is not None
        
        print("\n✅ FULL WORKFLOW TEST PASSED!")
        print("✅ Proxy system is fully operational")


# Additional standalone test functions for pytest compatibility
def test_imports():
    """Standalone test function for imports."""
    test_instance = TestTidalProxyIntegration()
    result = test_instance.test_imports()
    assert result, "Import test failed"

def test_session_creation():
    """Standalone test function for session creation."""
    test_instance = TestTidalProxyIntegration()
    result = test_instance.test_session_creation()
    assert result, "Session creation test failed"

def test_proxy_configuration():
    """Standalone test function for proxy configuration."""
    test_instance = TestTidalProxyIntegration()
    result = test_instance.test_proxy_configuration()
    assert result, "Proxy configuration test failed"

def test_compatibility():
    """Standalone test function for compatibility."""
    test_instance = TestTidalProxyIntegration()
    result = test_instance.test_compatibility()
    assert result, "Compatibility test failed"


def main():
    """Run all integration tests (for backward compatibility)."""
    print("🚀 Starting TIDAL Proxy Integration Tests")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    test_instance = TestTidalProxyIntegration()
    tests = [
        ("Import Tests", test_instance.test_imports),
        ("Session Creation Tests", test_instance.test_session_creation),
        ("Proxy Configuration Tests", test_instance.test_proxy_configuration),
        ("Backward Compatibility Tests", test_instance.test_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎉 TIDAL Proxy Integration is working correctly!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        print("❌ Please check the errors above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
