#!/usr/bin/env python3
"""Test script to verify centralized credentials are working correctly.

This script demonstrates that the centralized credentials system is functioning
properly across all test categories.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.network.credential_loader import (
    get_credential_loader,
    get_proxy_settings,
    get_network_settings,
    get_tidal_test_api_keys,
    get_tidal_environment_variables
)


def test_credential_loader_basic_functionality():
    """Test basic credential loader functionality."""
    print("=" * 60)
    print("TESTING CENTRALIZED CREDENTIALS SYSTEM")
    print("=" * 60)
    
    # Test credential loader initialization
    loader = get_credential_loader()
    info = loader.get_credentials_info()
    
    print(f"✓ Credential loader initialized successfully")
    print(f"  Version: {info['version']}")
    print(f"  Description: {info['description']}")
    print(f"  File path: {info['file_path']}")
    
    return True


def test_proxy_configurations():
    """Test all proxy configuration types."""
    print(f"\n" + "-" * 40)
    print("TESTING PROXY CONFIGURATIONS")
    print("-" * 40)
    
    proxy_types = ["primary", "test", "invalid", "disabled"]
    
    for proxy_type in proxy_types:
        try:
            proxy_settings = get_proxy_settings(proxy_type)
            print(f"✓ {proxy_type.capitalize()} proxy settings loaded:")
            print(f"  Enabled: {proxy_settings.enabled}")
            if proxy_settings.enabled:
                print(f"  HTTP Proxy: {proxy_settings.http_proxy}")
                print(f"  HTTPS Proxy: {proxy_settings.https_proxy}")
                if proxy_settings.username:
                    print(f"  Username: {proxy_settings.username[:10]}...")
                print(f"  Connection Timeout: {proxy_settings.connection_timeout}")
            print()
        except Exception as e:
            print(f"❌ Failed to load {proxy_type} proxy settings: {e}")
            return False
    
    return True


def test_network_configurations():
    """Test all network configuration types."""
    print("-" * 40)
    print("TESTING NETWORK CONFIGURATIONS")
    print("-" * 40)
    
    network_types = ["unit_tests", "integration_tests"]
    
    for network_type in network_types:
        try:
            network_settings = get_network_settings(network_type)
            print(f"✓ {network_type.replace('_', ' ').title()} network settings loaded:")
            print(f"  User Agent: {network_settings.user_agent}")
            print(f"  Connection Timeout: {network_settings.connection_timeout}")
            print(f"  Read Timeout: {network_settings.read_timeout}")
            print(f"  API Timeout: {network_settings.api_timeout}")
            print(f"  Retry Attempts: {network_settings.retry_attempts}")
            print(f"  Retry Backoff Factor: {network_settings.retry_backoff_factor}")
            print()
        except Exception as e:
            print(f"❌ Failed to load {network_type} network settings: {e}")
            return False
    
    return True


def test_tidal_configurations():
    """Test TIDAL-specific configurations."""
    print("-" * 40)
    print("TESTING TIDAL CONFIGURATIONS")
    print("-" * 40)
    
    try:
        # Test API keys
        api_keys = get_tidal_test_api_keys()
        print("✓ TIDAL test API keys loaded:")
        print(f"  Platform: {api_keys['platform']}")
        print(f"  Client ID: {api_keys['clientId']}")
        print(f"  Client Secret: {api_keys['clientSecret']}")
        print(f"  Valid: {api_keys['valid']}")
        print()
        
        # Test environment variables
        env_vars = get_tidal_environment_variables()
        print("✓ TIDAL environment variables configuration:")
        print(f"  Username var: {env_vars['username']}")
        print(f"  Password var: {env_vars['password']}")
        print(f"  Token var: {env_vars['token']}")
        print(f"  Refresh token var: {env_vars['refresh_token']}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load TIDAL configurations: {e}")
        return False


def test_fixture_compatibility():
    """Test that fixtures work correctly with centralized credentials."""
    print("-" * 40)
    print("TESTING FIXTURE COMPATIBILITY")
    print("-" * 40)
    
    try:
        # Test that different test categories get appropriate settings
        unit_network = get_network_settings("unit_tests")
        integration_network = get_network_settings("integration_tests")
        
        print("✓ Fixture compatibility verified:")
        print(f"  Unit tests use: {unit_network.user_agent}")
        print(f"  Integration tests use: {integration_network.user_agent}")
        
        # Verify they're different (as expected)
        if unit_network.user_agent != integration_network.user_agent:
            print("✓ Different test categories use appropriate settings")
        else:
            print("⚠️  Unit and integration tests use same user agent")
        
        # Test proxy settings for different categories
        test_proxy = get_proxy_settings("test")
        primary_proxy = get_proxy_settings("primary")
        
        print(f"  Unit tests use proxy: {test_proxy.http_proxy}")
        print(f"  Integration tests use proxy: {primary_proxy.http_proxy}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixture compatibility test failed: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid configurations."""
    print("-" * 40)
    print("TESTING ERROR HANDLING")
    print("-" * 40)
    
    try:
        # Test invalid proxy type
        try:
            get_proxy_settings("nonexistent")
            print("❌ Should have failed for nonexistent proxy type")
            return False
        except KeyError:
            print("✓ Correctly handles invalid proxy type")
        
        # Test invalid network type
        try:
            get_network_settings("nonexistent")
            print("❌ Should have failed for nonexistent network type")
            return False
        except KeyError:
            print("✓ Correctly handles invalid network type")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def main():
    """Run all tests and report results."""
    tests = [
        test_credential_loader_basic_functionality,
        test_proxy_configurations,
        test_network_configurations,
        test_tidal_configurations,
        test_fixture_compatibility,
        test_error_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Centralized credentials system is working correctly!")
        return 0
    else:
        print("❌ Some tests failed - please review the output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
