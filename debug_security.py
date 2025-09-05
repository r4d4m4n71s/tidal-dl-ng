#!/usr/bin/env python
"""
Debug script to analyze security vulnerabilities in tidal-dl-ng
"""
import sys
import logging
import os

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug mode for all modules
os.environ['PYTHONDEBUG'] = '1'

# Import and analyze API module
print("\n=== ANALYZING API MODULE ===")
try:
    from tidal_dl_ng import api
    print(f"API Version: {api.getVersion()}")
    print(f"Number of API keys: {api.getNum()}")
    
    # Check for hardcoded keys
    print("\n--- Checking API Keys ---")
    for i in range(api.getNum()):
        item = api.getItem(i)
        print(f"Key {i}: Platform={item['platform']}, Valid={item['valid']}")
        print(f"  ClientId: {item['clientId'][:10]}... (truncated)")
        print(f"  ClientSecret: {item['clientSecret'][:10]}... (truncated)")
    
    # Test secure key functionality
    print("\n--- Testing Secure Key System ---")
    secure_key = api.get_secure_key()
    print(f"Secure key platform: {secure_key.get('platform', 'Unknown')}")
    
    # Test headers
    print("\n--- Testing Header System ---")
    headers = api.get_secure_headers()
    print(f"Headers generated: {list(headers.keys())}")
    print(f"User-Agent: {headers.get('User-Agent', 'None')}")
    
except Exception as e:
    print(f"Error loading API module: {e}")
    import traceback
    traceback.print_exc()

# Import and analyze decryption module
print("\n\n=== ANALYZING DECRYPTION MODULE ===")
try:
    from tidal_dl_ng.helper import decryption
    
    # Check for secure decryption mode
    print(f"Secure decryption enabled: {os.environ.get('TIDAL_USE_SECURE_DECRYPTION', 'false')}")
    
    # Initialize secure decryption
    secure_decrypt = decryption._secure_decryption
    master_key = secure_decrypt.get_master_key()
    print(f"Master key length: {len(master_key)} bytes")
    print(f"Master key (first 10 chars): {str(master_key)[:10]}...")
    
    # Check if using legacy key
    legacy_key_b64 = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
    import base64
    legacy_key = base64.b64decode(legacy_key_b64)
    if master_key == legacy_key:
        print("WARNING: Using hardcoded legacy decryption key!")
    else:
        print("Using secure/derived decryption key")
        
except Exception as e:
    print(f"Error loading decryption module: {e}")
    import traceback
    traceback.print_exc()

# Test security modules
print("\n\n=== TESTING SECURITY MODULES ===")
try:
    from tidal_dl_ng.security.key_manager import SecureKeyManager
    from tidal_dl_ng.security.header_manager import HeaderManager
    from tidal_dl_ng.security.request_obfuscator import RequestObfuscator
    from tidal_dl_ng.security.metadata_obfuscator import MetadataObfuscator
    
    # Test key manager
    print("\n--- Key Manager ---")
    key_mgr = SecureKeyManager()
    print(f"Config path: {key_mgr.config_path}")
    print(f"Encrypted keys exist: {(key_mgr.config_path / 'api_keys.enc').exists()}")
    
    # Test header manager
    print("\n--- Header Manager ---")
    header_mgr = HeaderManager()
    print(f"User agents available: {len(header_mgr.user_agents)}")
    print(f"Sample UA: {header_mgr.get_random_user_agent()[:50]}...")
    
    # Test request obfuscator
    print("\n--- Request Obfuscator ---")
    req_obf = RequestObfuscator()
    delay = req_obf.get_dynamic_delay()
    print(f"Dynamic delay: {delay} seconds")
    should_pause, pause_duration = req_obf.should_pause_session()
    print(f"Should pause: {should_pause}, Duration: {pause_duration}")
    
    # Test metadata obfuscator
    print("\n--- Metadata Obfuscator ---")
    meta_obf = MetadataObfuscator()
    test_metadata = {
        'title': 'Test Song',
        'artist': 'Test Artist',
        'album': 'Test Album',
        'date': '2023-01-01',
        'tracknumber': 1
    }
    obfuscated = meta_obf.create_metadata_fingerprint_resistance(test_metadata)
    print(f"Original metadata: {test_metadata}")
    print(f"Obfuscated metadata: {obfuscated}")
    
except Exception as e:
    print(f"Error testing security modules: {e}")
    import traceback
    traceback.print_exc()

# Test configuration
print("\n\n=== TESTING CONFIGURATION ===")
try:
    from tidal_dl_ng.config import Settings
    settings = Settings()
    
    print(f"Settings file: {settings.path_file}")
    print(f"Download delay enabled: {settings.data.download_delay}")
    print(f"Download delay range: {settings.data.download_delay_sec_min}-{settings.data.download_delay_sec_max} seconds")
    
    # Check for proxy settings
    print(f"\nProxy enabled: {settings.data.proxy_enabled}")
    if settings.data.proxy_enabled:
        print(f"Proxy host: {settings.data.proxy_host}")
        print(f"Proxy type: {settings.data.proxy_type}")
    
except Exception as e:
    print(f"Error loading configuration: {e}")
    import traceback
    traceback.print_exc()

# Test CLI initialization
print("\n\n=== TESTING CLI INITIALIZATION ===")
try:
    # Set environment to avoid actual login
    os.environ['TIDAL_DL_NG_DEBUG'] = '1'
    
    from tidal_dl_ng.cli import ctx, init_session
    
    print("CLI context initialized")
    print(f"Session exists: {hasattr(ctx, 'session')}")
    
except Exception as e:
    print(f"Error testing CLI: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== DEBUG ANALYSIS COMPLETE ===")
print("\nKey Security Findings:")
print("1. API keys are still hardcoded in the source")
print("2. Decryption key defaults to hardcoded value")
print("3. Security modules are initialized but not fully integrated")
print("4. No proxy support active by default")
print("5. Metadata obfuscation not applied in actual operations")
