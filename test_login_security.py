#!/usr/bin/env python
"""
Test login and API key usage security
"""
import os
import logging

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test with secure mode enabled
print("\n=== TESTING WITH SECURE MODE ENABLED ===")
os.environ['TIDAL_USE_SECURE_DECRYPTION'] = 'true'

from tidal_dl_ng import api
from tidal_dl_ng.helper import decryption

# Check decryption mode
secure_decrypt = decryption._secure_decryption
master_key = secure_decrypt.get_master_key()
print(f"Master key length: {len(master_key)} bytes")

# Check if still using legacy key
legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
import base64
legacy_key = base64.b64decode(legacy_key_b64)
if master_key == legacy_key:
    print("WARNING: Still using hardcoded legacy decryption key even in secure mode!")
else:
    print("SUCCESS: Using derived decryption key in secure mode")

# Test API key rotation
print("\n=== TESTING API KEY ROTATION ===")
for i in range(10):
    key = api.get_secure_key()
    print(f"Rotation {i}: Platform={key.get('platform')}, ClientId={key.get('clientId')[:10]}...")

# Test header generation variety
print("\n=== TESTING HEADER VARIETY ===")
from collections import Counter
user_agents = []
for i in range(20):
    headers = api.get_secure_headers()
    user_agents.append(headers.get('User-Agent', ''))

ua_counts = Counter(user_agents)
print(f"Unique User-Agents generated: {len(ua_counts)}")
for ua, count in ua_counts.most_common(5):
    print(f"  {ua[:50]}... (used {count} times)")

# Test proxy configuration
print("\n=== TESTING PROXY CONFIGURATION ===")
from tidal_dl_ng.config import Settings
try:
    settings = Settings()
    print(f"Proxy enabled: {settings.data.proxy_enabled}")
    print(f"Proxy host: {settings.data.proxy_host}")
    print(f"Proxy type: {settings.data.proxy_type}")
    print(f"Proxy auth enabled: {settings.data.proxy_use_auth}")
except Exception as e:
    print(f"Error accessing settings: {e}")

# Test download patterns
print("\n=== TESTING DOWNLOAD PATTERNS ===")
from tidal_dl_ng.security.request_obfuscator import RequestObfuscator
obf = RequestObfuscator()

# Test timing patterns
delays = []
for i in range(10):
    delay = obf.get_dynamic_delay()
    delays.append(delay)

print(f"Delay range: {min(delays):.2f} - {max(delays):.2f} seconds")
print(f"Average delay: {sum(delays)/len(delays):.2f} seconds")

# Test download order randomization
items = list(range(20))
randomized = obf.randomize_download_order(items)
print(f"\nOriginal order: {items}")
print(f"Randomized order: {randomized}")
print(f"Order changed: {items != randomized}")

print("\n=== SECURITY TEST COMPLETE ===")
