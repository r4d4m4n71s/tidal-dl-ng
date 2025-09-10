import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from tests.network.credential_loader import get_proxy_settings, get_network_settings
from tidal_dl_ng.network import NetworkManager
from tidal_dl_ng.config import Tidal

print("=== Testing Proxy Authentication Fix ===")

# Load credentials
proxy_settings = get_proxy_settings("primary")
network_settings = get_network_settings("integration_tests")

print(f"Original proxy credentials:")
print(f"  Username: {proxy_settings.username}")
print(f"  Password: {proxy_settings.password[:10]}...")
print(f"  HTTP Proxy: {proxy_settings.http_proxy}")

# Configure NetworkManager
network_manager = NetworkManager()
network_manager.configure(network_settings, proxy_settings)

# Get auth session
auth_session = network_manager.get_session("auth")

print(f"\nSession proxy configuration after fix:")
print(f"  Proxies: {auth_session.proxies}")
print(f"  Auth: {auth_session.auth}")

# Check if credentials are embedded in URLs
http_proxy = auth_session.proxies.get('http', '')
https_proxy = auth_session.proxies.get('https', '')

credentials_embedded = '@' in http_proxy and '@' in https_proxy
print(f"\nCredentials embedded in URLs: {'✓ YES' if credentials_embedded else '❌ NO'}")

if credentials_embedded:
    print("✓ Fix applied successfully - credentials are now embedded in proxy URLs")
    print("✓ session.auth should be None (no longer used for proxy auth)")
else:
    print("❌ Fix not working - credentials still not embedded")

# Test if the proxy authentication works now
print(f"\nTesting proxy authentication...")
try:
    # Try to make a simple request through the proxy
    response = auth_session.get("https://httpbin.org/ip", timeout=10)
    print(f"  Request successful: {response.status_code}")
    print(f"  Response: {response.text[:100]}...")
    print("✓ Proxy authentication working!")
except Exception as e:
    print(f"  Request failed: {e}")
    print(f"  Error type: {type(e)}")
    if "407" in str(e):
        print("❌ Still getting 407 Proxy Authentication Required")
    else:
        print("⚠️  Different error - may be network/proxy server issue")

print("\n=== End Test ===")
