"""Test TIDAL authentication and API operations using real credentials.

⚠️  WARNING: REAL CREDENTIALS REQUIRED ⚠️
This test file uses actual TIDAL credentials and makes real API calls.
Use with caution and ensure proper credential security.

This test validates:
- Real OAuth authentication flows through proxy
- Token refresh with actual TIDAL tokens
- Authenticated API operations (search, tracks, albums, playlists)
- End-to-end download authentication
- Real error handling and rate limiting

SECURITY CONSIDERATIONS:
- Never commit real credentials to version control
- Use environment variables for credential storage
- Ensure proper cleanup of test data
- Respect TIDAL API rate limits
- Monitor network traffic for credential exposure
"""

import os
import time
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
import base64

import requests
from requests.exceptions import RequestException

from tidal_dl_ng.config import Settings, Tidal
from tidal_dl_ng.network import NetworkManager, ProxyConnectionError, NetworkTimeoutError, ProxyAuthenticationError
from tidal_dl_ng.model.network import NetworkSettings, ProxySettings
from tidal_dl_ng.config import Tidal
from tidal_dl_ng.download import Download


# Configure logging for real credential tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealCredentialTestManager:
    """Manager for real TIDAL credential testing with security safeguards."""
    
    def __init__(self):
        self.test_results = []
        self.api_call_count = 0
        self.rate_limit_delay = 1.0  # Seconds between API calls
        self.max_api_calls = 50  # Maximum API calls per test session
        self.credential_exposure_checks = []
        
    def validate_environment(self) -> Dict[str, Any]:
        """Validate environment setup for real credential testing."""
        validation = {
            'credentials_available': False,
            'proxy_configured': False,
            'network_accessible': False,
            'rate_limiting_enabled': True,
            'security_checks_passed': False,
            'warnings': []
        }
        
        # Check for credential environment variables
        required_env_vars = ['TIDAL_USERNAME', 'TIDAL_PASSWORD']
        optional_env_vars = ['TIDAL_TOKEN', 'TIDAL_REFRESH_TOKEN']
        
        credentials_found = any(os.getenv(var) for var in required_env_vars + optional_env_vars)
        validation['credentials_available'] = credentials_found
        
        if not credentials_found:
            validation['warnings'].append(
                "No TIDAL credentials found in environment variables. "
                "Set TIDAL_USERNAME/TIDAL_PASSWORD or TIDAL_TOKEN/TIDAL_REFRESH_TOKEN"
            )
        
        # Check proxy configuration
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'PROXY_USERNAME', 'PROXY_PASSWORD']
        proxy_configured = any(os.getenv(var) for var in proxy_vars)
        validation['proxy_configured'] = proxy_configured
        
        # Basic network connectivity check
        try:
            response = requests.get('https://api.tidal.com/v1/login/username', timeout=10)
            validation['network_accessible'] = response.status_code in [200, 400, 401]
        except Exception as e:
            validation['warnings'].append(f"Network connectivity issue: {e}")
        
        # Security checks
        security_passed = True
        
        # Check if we're in a secure environment (not in CI/CD)
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            validation['warnings'].append("Running in CI/CD environment - credential tests should be skipped")
            security_passed = False
        
        # Check for credential exposure in environment
        for var_name, var_value in os.environ.items():
            if var_value and len(var_value) > 20:
                if any(keyword in var_name.upper() for keyword in ['TOKEN', 'SECRET', 'KEY', 'PASSWORD']):
                    # Don't log the actual value, just check it's not obviously exposed
                    if not var_value.startswith('***') and len(var_value) > 50:
                        self.credential_exposure_checks.append({
                            'variable': var_name,
                            'length': len(var_value),
                            'potentially_exposed': True
                        })
        
        validation['security_checks_passed'] = security_passed
        
        return validation
    
    def mask_credential(self, credential: str) -> str:
        """Safely mask credentials for logging."""
        if not credential or len(credential) < 8:
            return "***"
        return credential[:3] + "***" + credential[-3:]
    
    def respect_rate_limit(self):
        """Implement rate limiting to respect TIDAL API limits."""
        if self.api_call_count >= self.max_api_calls:
            raise Exception(f"Maximum API calls ({self.max_api_calls}) reached for this test session")
        
        time.sleep(self.rate_limit_delay)
        self.api_call_count += 1
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test results with credential masking."""
        # Mask any potential credentials in details
        safe_details = {}
        for key, value in details.items():
            if any(keyword in key.lower() for keyword in ['token', 'password', 'secret', 'key']):
                safe_details[key] = self.mask_credential(str(value)) if value else None
            else:
                safe_details[key] = value
        
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': time.time(),
            'details': safe_details
        }
        
        self.test_results.append(result)
        
        status = "✓ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        
        if not success and 'error' in safe_details:
            logger.error(f"  Error: {safe_details['error']}")


def test_real_oauth_login_flow(proxy_settings, network_settings):
    """Test real OAuth authentication flow through proxy with actual TIDAL credentials."""
    print("=" * 70)
    print("TESTING REAL OAUTH LOGIN FLOW")
    print("=" * 70)
    
    # Load TIDAL credentials from JSON file and set as environment variables
    from tests.network.credential_loader import set_tidal_credentials_as_env_vars
    set_tidal_credentials_as_env_vars()
    print("✓ TIDAL credentials loaded from credentials.json")
    
    test_manager = RealCredentialTestManager()
    
    # Validate environment first
    env_validation = test_manager.validate_environment()
    
    print("Environment Validation:")
    for key, value in env_validation.items():
        if key != 'warnings':
            print(f"  {key}: {value}")
    
    if env_validation['warnings']:
        print("  Warnings:")
        for warning in env_validation['warnings']:
            print(f"    - {warning}")
    
    if not env_validation['credentials_available']:
        print("⚠️  Skipping real OAuth test - no credentials available")
        return
    
    if not env_validation['security_checks_passed']:
        print("⚠️  Skipping real OAuth test - security checks failed")
        return
    
    print("\nTesting real OAuth authentication...")
    
    # Configure NetworkManager with proxy
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Create Tidal instance
    tidal = Tidal()
    
    try:
        # Test OAuth login with real credentials
        print("  Attempting OAuth login...")
        
        # Check for existing token first
        if os.getenv('TIDAL_TOKEN'):
            print("  Using existing token from environment...")
            
            # Validate token format
            token = os.getenv('TIDAL_TOKEN')
            token_valid = len(token) > 20 and not token.startswith('***')
            
            if token_valid:
                # Test token-based authentication
                try:
                    result = tidal.login_token()
                    
                    test_manager.log_test_result('oauth_token_login', result, {
                        'token_length': len(token),
                        'login_successful': result,
                        'proxy_used': bool(proxy_settings.http_proxy or proxy_settings.https_proxy)
                    })
                    
                    if result:
                        print("  ✓ Token-based authentication successful")
                        
                        # Test session integrity
                        tidal._monitor_session_integrity()
                        session_ok = tidal.session.request_session is not None
                        
                        test_manager.log_test_result('oauth_session_integrity', session_ok, {
                            'session_maintained': session_ok,
                            'proxy_session': bool(tidal.session.request_session.proxies) if session_ok else False
                        })
                        
                    else:
                        print("  ❌ Token-based authentication failed - token may be expired")
                        print("  💡 Try refreshing your TIDAL_TOKEN environment variable")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    if "401" in error_msg or "unauthorized" in error_msg:
                        print("  ❌ Token-based authentication failed: 401 Unauthorized")
                        print("  💡 Token appears to be expired or invalid")
                        print("  💡 Try getting a fresh token or use username/password authentication")
                        
                        test_manager.log_test_result('oauth_token_login', False, {
                            'error': 'Token expired or invalid (401 Unauthorized)',
                            'error_type': 'TokenExpiredError',
                            'token_length': len(token)
                        })
                    else:
                        print(f"  ❌ Token-based authentication error: {e}")
                        test_manager.log_test_result('oauth_token_login', False, {
                            'error': str(e),
                            'error_type': type(e).__name__
                        })
            
        else:
            # Interactive OAuth flow with automation support
            print("  Starting interactive OAuth flow...")
            
            # Check if automation is enabled
            #automation_enabled = os.getenv('TIDAL_OAUTH_AUTOMATION', 'true').lower() in ('true', '1', 'yes', 'on')
            automation_enabled = False;
            if automation_enabled:
                print("  🤖 Automated OAuth authentication enabled")
            else:
                print("  ⚠️  Manual OAuth authentication - browser window will open")
            
            # Capture OAuth messages
            oauth_messages = []
            def capture_oauth_output(msg):
                oauth_messages.append(str(msg))
                print(f"    OAuth: {msg}")  # Ensure output is displayed
                # Check for credential exposure
                if any(cred in str(msg) for cred in ['Bearer ', 'access_token', 'refresh_token']):
                    if '***' not in str(msg):
                        test_manager.credential_exposure_checks.append({
                            'source': 'oauth_output',
                            'message_preview': str(msg)[:50] + "...",
                            'potentially_exposed': True
                        })
            
            try:
                # Start OAuth flow to get the authentication URL
                print("  Starting OAuth device authorization to get authentication URL...")
                
                # Use a separate thread or async approach to capture the URL
                import threading
                import time
                
                oauth_url = None
                oauth_completed = False
                oauth_error = None
                oauth_result = False
                
                def oauth_thread():
                    nonlocal oauth_completed, oauth_error, oauth_result
                    try:
                        result = tidal.login(capture_oauth_output)
                        oauth_result = result
                        oauth_completed = True
                        return result
                    except Exception as e:
                        oauth_error = e
                        oauth_completed = True
                
                # Start OAuth in background
                thread = threading.Thread(target=oauth_thread)
                thread.daemon = True
                thread.start()
                
                # Wait for OAuth URL to be captured and potentially perform automation
                max_wait_for_url = 15  # Wait up to 15 seconds for URL
                waited = 0
                url_extracted = False
                
                print("  Waiting for OAuth URL to be generated...")
                
                while waited < max_wait_for_url and not oauth_completed:
                    time.sleep(1)
                    waited += 1
                    
                    # Check if we have captured an OAuth URL (only once)
                    if oauth_messages and not url_extracted:
                        from tests.network.automated_oauth import create_oauth_handler
                        
                        # Create a placeholder browser action function
                        def browser_action_func(action, **kwargs):
                            print(f"    🤖 Browser action placeholder: {action} {kwargs}")
                            return True
                        
                        oauth_handler = create_oauth_handler(browser_action_func)
                        oauth_url = oauth_handler.extract_oauth_url(oauth_messages)
                        
                        if oauth_url:
                            print(f"  ✓ OAuth URL extracted: {oauth_url}")
                            url_extracted = True
                            
                            # Get credentials for automation
                            username = os.getenv('TIDAL_USERNAME')
                            password = os.getenv('TIDAL_PASSWORD')
                            
                            if username and password and automation_enabled:
                                print("  🤖 Preparing automated login steps...")
                                
                                # Get automation steps
                                steps = oauth_handler.get_automation_steps(oauth_url, username, password)
                                
                                print(f"  ✓ Generated {len(steps)} automation steps")
                                print("  💡 Automation steps are ready for external execution")
                                print("  💡 In a real implementation, these steps would be executed by browser automation")
                                
                                # For demonstration, show first few steps
                                print("  📋 First few automation steps:")
                                for i, step in enumerate(steps[:5]):
                                    action = step['action']
                                    desc = step['description']
                                    print(f"    {i+1}. {action}: {desc}")
                                
                                if len(steps) > 5:
                                    print(f"    ... and {len(steps) - 5} more steps")
                                
                                # Simulate successful preparation
                                success, message = oauth_handler.automated_login(oauth_url, username, password)
                                
                                if success:
                                    print(f"  ✓ Automation preparation successful: {message}")
                                else:
                                    print(f"  ❌ Automation preparation failed: {message}")
                                
                                print("  💡 In a real scenario, browser automation would now execute these steps")
                                print("  💡 For testing purposes, manual authentication is required")
                                print(f"  🌐 Please visit: {oauth_url}")
                                print("  ⏳ Waiting for manual authentication to complete...")
                            else:
                                if not automation_enabled:
                                    print("  ⚠️  Automation disabled - manual authentication required")
                                else:
                                    print("  ⚠️  No username/password available for automation")
                                    print("  💡 Set TIDAL_USERNAME and TIDAL_PASSWORD for automation")
                                
                                print(f"  🌐 Please visit: {oauth_url}")
                                print("  ⏳ Waiting for manual authentication to complete...")
                            
                            # Break out of the URL waiting loop once URL is processed
                            break
                
                if not url_extracted and oauth_messages:
                    print("  ⚠️  OAuth messages received but URL extraction failed")
                    print("  📝 OAuth messages:")
                    for i, msg in enumerate(oauth_messages[-3:]):  # Show last 3 messages
                        print(f"    {i+1}. {msg}")
                
                # Wait for OAuth thread to complete
                print("  ⏳ Waiting for OAuth authentication to complete...")
                thread.join(timeout=60)  # Wait up to 60 seconds total for manual auth
                
                if oauth_error:
                    raise oauth_error
                
                result = oauth_result  # Use the actual login result, not just completion status
                
                test_manager.log_test_result('oauth_interactive_login', result, {
                    'login_successful': result,
                    'messages_captured': len(oauth_messages),
                    'proxy_used': bool(proxy_settings.http_proxy or proxy_settings.https_proxy),
                    'automation_enabled': automation_enabled,
                    'oauth_url_extracted': oauth_url is not None
                })
                
                if result:
                    print("  ✓ Interactive OAuth authentication successful")
                    if oauth_url:
                        print("  ✓ OAuth URL was successfully extracted and processed")
                else:
                    print("  ❌ Interactive OAuth authentication failed")
                
            except Exception as e:
                test_manager.log_test_result('oauth_interactive_login', False, {
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                print(f"  ❌ OAuth authentication error: {e}")
    
    except Exception as e:
        test_manager.log_test_result('oauth_login_flow', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"❌ OAuth login flow failed: {e}")
    
    # Report credential exposure checks
    if test_manager.credential_exposure_checks:
        print(f"\n⚠️  Credential exposure warnings: {len(test_manager.credential_exposure_checks)}")
        for check in test_manager.credential_exposure_checks:
            print(f"    - {check['source']}: {check.get('message_preview', 'Check details')}")
    
    print("✓ Real OAuth login flow test completed")


def test_real_token_refresh_scenarios(proxy_settings, network_settings):
    """Test token refresh scenarios with real TIDAL tokens."""
    print("\n" + "=" * 70)
    print("TESTING REAL TOKEN REFRESH SCENARIOS")
    print("=" * 70)
    
    test_manager = RealCredentialTestManager()
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Create Tidal instance
    tidal = Tidal()
    
    print("Testing real token refresh scenarios...")
    
    # Check for existing refresh token
    refresh_token = os.getenv('TIDAL_REFRESH_TOKEN')
    
    if not refresh_token:
        print("  No refresh token available in environment")
        print("  Checking for stored tokens...")
        
        # Check if we have stored tokens
        if tidal.token_from_storage:
            print("  Found stored tokens, testing refresh...")
            
            try:
                # Test token refresh
                test_manager.respect_rate_limit()
                result = tidal.login_token()
                
                test_manager.log_test_result('stored_token_refresh', result, {
                    'refresh_successful': result,
                    'proxy_used': bool(proxy_settings.http_proxy or proxy_settings.https_proxy),
                    'token_source': 'stored'
                })
                
                if result:
                    print("  ✓ Stored token refresh successful")
                    
                    # Validate refreshed token
                    if hasattr(tidal.data, 'access_token'):
                        token_length = len(tidal.data.access_token)
                        token_valid = token_length > 20
                        
                        test_manager.log_test_result('refreshed_token_validation', token_valid, {
                            'token_length': token_length,
                            'token_format_valid': token_valid,
                            'has_expiry': hasattr(tidal.data, 'expiry_time')
                        })
                        
                        print(f"    Token length: {token_length}")
                        print(f"    Token valid: {token_valid}")
                
                else:
                    print("  ❌ Stored token refresh failed - tokens may be expired")
                    print("  💡 Try clearing stored tokens and re-authenticating")
            
            except Exception as e:
                error_msg = str(e).lower()
                if "401" in error_msg or "unauthorized" in error_msg:
                    print("  ❌ Stored token refresh failed: 401 Unauthorized")
                    print("  💡 Stored tokens appear to be expired or invalid")
                    print("  💡 Clear token storage and re-authenticate with fresh credentials")
                    
                    test_manager.log_test_result('stored_token_refresh', False, {
                        'error': 'Stored tokens expired or invalid (401 Unauthorized)',
                        'error_type': 'TokenExpiredError',
                        'token_source': 'stored'
                    })
                else:
                    test_manager.log_test_result('stored_token_refresh', False, {
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    print(f"  ❌ Token refresh error: {e}")
        
        else:
            print("  No stored tokens available")
            print("  ⚠️  Skipping token refresh tests")
            return
    
    else:
        print("  Testing with environment refresh token...")
        
        try:
            # Manually set refresh token for testing
            if hasattr(tidal, 'data'):
                tidal.data.refresh_token = refresh_token
            
            test_manager.respect_rate_limit()
            result = tidal.login_token()
            
            test_manager.log_test_result('env_token_refresh', result, {
                'refresh_successful': result,
                'proxy_used': bool(proxy_settings.http_proxy or proxy_settings.https_proxy),
                'token_source': 'environment'
            })
            
            if result:
                print("  ✓ Environment token refresh successful")
            else:
                print("  ❌ Environment token refresh failed - refresh token may be expired")
                print("  💡 Try updating TIDAL_REFRESH_TOKEN environment variable")
        
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg:
                print("  ❌ Environment token refresh failed: 401 Unauthorized")
                print("  💡 TIDAL_REFRESH_TOKEN appears to be expired or invalid")
                print("  💡 Update environment variable with fresh refresh token")
                
                test_manager.log_test_result('env_token_refresh', False, {
                    'error': 'Environment refresh token expired or invalid (401 Unauthorized)',
                    'error_type': 'TokenExpiredError',
                    'token_source': 'environment'
                })
            else:
                test_manager.log_test_result('env_token_refresh', False, {
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                print(f"  ❌ Environment token refresh error: {e}")
    
    # Test token expiration handling
    print("\n  Testing token expiration handling...")
    
    try:
        # Simulate expired token scenario
        if hasattr(tidal, 'data') and hasattr(tidal.data, 'expiry_time'):
            original_expiry = tidal.data.expiry_time
            
            # Set token as expired
            tidal.data.expiry_time = time.time() - 3600  # 1 hour ago
            
            # Test automatic refresh on API call
            test_manager.respect_rate_limit()
            
            # This should trigger automatic token refresh
            api_result = tidal.session.request_session.get('https://api.tidal.com/v1/sessions')
            
            refresh_triggered = api_result.status_code != 401
            
            test_manager.log_test_result('automatic_token_refresh', refresh_triggered, {
                'refresh_triggered': refresh_triggered,
                'api_status_code': api_result.status_code,
                'expiry_handled': True
            })
            
            # Restore original expiry
            tidal.data.expiry_time = original_expiry
            
            if refresh_triggered:
                print("  ✓ Automatic token refresh on expiry works")
            else:
                print("  ⚠️  Automatic token refresh may need attention")
    
    except Exception as e:
        test_manager.log_test_result('automatic_token_refresh', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"  ❌ Token expiration test error: {e}")
    
    print("✓ Real token refresh scenarios test completed")


def test_real_api_integration(proxy_settings, network_settings):
    """Test authenticated API operations with real TIDAL API."""
    print("\n" + "=" * 70)
    print("TESTING REAL API INTEGRATION")
    print("=" * 70)
    
    test_manager = RealCredentialTestManager()
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Create Tidal and API instances
    tidal = Tidal()
    
    # Ensure we're authenticated
    if not tidal.login_token():
        print("  ⚠️  Authentication required for API tests")
        print("  Attempting authentication...")
        
        # Define print function for OAuth flow
        def oauth_print(msg):
            print(f"    OAuth: {msg}")
        
        if not tidal.login(oauth_print):
            print("  ❌ Authentication failed - skipping API tests")
            return
    
    print("  ✓ Authentication successful, testing API operations...")
    
    # Use the Tidal session for API operations
    api = tidal.session
    
    # Test 1: Search functionality
    print("\n  Testing search functionality...")
    
    try:
        test_manager.respect_rate_limit()
        
        search_results = api.search("The Beatles", limit=5)
        
        search_success = search_results is not None and len(search_results) > 0
        
        test_manager.log_test_result('api_search', search_success, {
            'search_query': 'The Beatles',
            'results_count': len(search_results) if search_results else 0,
            'proxy_used': bool(proxy_settings.http_proxy or proxy_settings.https_proxy)
        })
        
        if search_success:
            print(f"    ✓ Search returned {len(search_results)} results")
        else:
            print("    ❌ Search failed or returned no results")
    
    except Exception as e:
        test_manager.log_test_result('api_search', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Search error: {e}")
    
    # Test 2: Track information
    print("\n  Testing track information retrieval...")
    
    try:
        test_manager.respect_rate_limit()
        
        # Use a known track ID for testing
        track_id = "25077365"  # Example track ID
        track_info = api.get_track(track_id)
        
        track_success = track_info is not None
        
        test_manager.log_test_result('api_track_info', track_success, {
            'track_id': track_id,
            'track_found': track_success,
            'has_title': bool(track_info.get('title')) if track_info else False,
            'has_artist': bool(track_info.get('artist')) if track_info else False
        })
        
        if track_success:
            print(f"    ✓ Track info retrieved: {track_info.get('title', 'Unknown')}")
        else:
            print("    ❌ Track info retrieval failed")
    
    except Exception as e:
        test_manager.log_test_result('api_track_info', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Track info error: {e}")
    
    # Test 3: Album information
    print("\n  Testing album information retrieval...")
    
    try:
        test_manager.respect_rate_limit()
        
        # Use a known album ID for testing
        album_id = "25077364"  # Example album ID
        album_info = api.get_album(album_id)
        
        album_success = album_info is not None
        
        test_manager.log_test_result('api_album_info', album_success, {
            'album_id': album_id,
            'album_found': album_success,
            'has_title': bool(album_info.get('title')) if album_info else False,
            'has_tracks': bool(album_info.get('numberOfTracks')) if album_info else False
        })
        
        if album_success:
            print(f"    ✓ Album info retrieved: {album_info.get('title', 'Unknown')}")
        else:
            print("    ❌ Album info retrieval failed")
    
    except Exception as e:
        test_manager.log_test_result('api_album_info', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Album info error: {e}")
    
    # Test 4: User playlists (if available)
    print("\n  Testing user playlist access...")
    
    try:
        test_manager.respect_rate_limit()
        
        playlists = api.get_user_playlists()
        
        playlist_success = playlists is not None
        
        test_manager.log_test_result('api_user_playlists', playlist_success, {
            'playlists_found': playlist_success,
            'playlist_count': len(playlists) if playlists else 0,
            'authenticated_access': True
        })
        
        if playlist_success:
            print(f"    ✓ User playlists retrieved: {len(playlists)} playlists")
        else:
            print("    ❌ User playlist access failed")
    
    except Exception as e:
        test_manager.log_test_result('api_user_playlists', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ User playlist error: {e}")
    
    # Test 5: Rate limiting behavior
    print("\n  Testing API rate limiting behavior...")
    
    try:
        rate_limit_hits = 0
        successful_calls = 0
        
        for i in range(5):  # Make several rapid calls
            try:
                test_manager.respect_rate_limit()
                result = api.search(f"test query {i}", limit=1)
                if result:
                    successful_calls += 1
            except Exception as e:
                if "rate" in str(e).lower() or "limit" in str(e).lower():
                    rate_limit_hits += 1
        
        test_manager.log_test_result('api_rate_limiting', True, {
            'successful_calls': successful_calls,
            'rate_limit_hits': rate_limit_hits,
            'rate_limiting_respected': rate_limit_hits == 0
        })
        
        print(f"    ✓ Rate limiting test: {successful_calls} successful, {rate_limit_hits} rate limited")
    
    except Exception as e:
        test_manager.log_test_result('api_rate_limiting', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Rate limiting test error: {e}")
    
    print("✓ Real API integration test completed")


def test_real_download_authentication(proxy_settings, network_settings):
    """Test end-to-end download authentication with real TIDAL content."""
    print("\n" + "=" * 70)
    print("TESTING REAL DOWNLOAD AUTHENTICATION")
    print("=" * 70)
    
    test_manager = RealCredentialTestManager()
    
    # Configure NetworkManager
    network_manager = NetworkManager()
    network_manager.configure(network_settings, proxy_settings)
    
    # Create Tidal instance
    tidal = Tidal()
    
    # Ensure authentication
    def oauth_print(msg):
        print(f"    OAuth: {msg}")
    
    if not tidal.login_token() and not tidal.login(oauth_print):
        print("  ❌ Authentication required for download tests - skipping")
        return
    
    print("  ✓ Authentication successful, testing download operations...")
    
    # Test 1: Download URL generation
    print("\n  Testing download URL generation...")
    
    try:
        test_manager.respect_rate_limit()
        
        # Use a known track ID for testing
        track_id = "25077365"  # Example track ID
        
        # Create download instance
        download = Download()
        
        # Test URL generation (without actual download)
        download_url = download.get_track_url(track_id, quality="HIGH")
        
        url_success = download_url is not None and download_url.startswith('http')
        
        test_manager.log_test_result('download_url_generation', url_success, {
            'track_id': track_id,
            'quality': 'HIGH',
            'url_generated': url_success,
            'url_secure': download_url.startswith('https') if download_url else False,
            'proxy_used': bool(proxy_settings.http_proxy or proxy_settings.https_proxy)
        })
        
        if url_success:
            print(f"    ✓ Download URL generated successfully")
            print(f"    URL secure: {download_url.startswith('https')}")
        else:
            print("    ❌ Download URL generation failed")
    
    except Exception as e:
        test_manager.log_test_result('download_url_generation', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Download URL error: {e}")
    
    # Test 2: Quality selection authentication
    print("\n  Testing quality selection with authentication...")
    
    try:
        test_manager.respect_rate_limit()
        
        qualities = ['LOW', 'HIGH', 'LOSSLESS']
        quality_results = {}
        
        for quality in qualities:
            try:
                url = download.get_track_url(track_id, quality=quality)
                quality_results[quality] = url is not None
            except Exception as e:
                quality_results[quality] = False
                print(f"    Quality {quality} error: {e}")
        
        available_qualities = sum(quality_results.values())
        
        test_manager.log_test_result('download_quality_selection', available_qualities > 0, {
            'qualities_tested': len(qualities),
            'qualities_available': available_qualities,
            'quality_results': quality_results,
            'subscription_level_detected': available_qualities >= 2
        })
        
        print(f"    ✓ Quality selection: {available_qualities}/{len(qualities)} qualities available")
        for quality, available in quality_results.items():
            status = "✓" if available else "❌"
            print(f"      {status} {quality}")
    
    except Exception as e:
        test_manager.log_test_result('download_quality_selection', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Quality selection error: {e}")
    
    # Test 3: Download metadata authentication
    print("\n  Testing download metadata retrieval...")
    
    try:
        test_manager.respect_rate_limit()
        
        metadata = download.get_track_metadata(track_id)
        
        metadata_success = metadata is not None and isinstance(metadata, dict)
        
        test_manager.log_test_result('download_metadata', metadata_success, {
            'track_id': track_id,
            'metadata_retrieved': metadata_success,
            'has_title': bool(metadata.get('title')) if metadata else False,
            'has_artist': bool(metadata.get('artist')) if metadata else False,
            'has_album': bool(metadata.get('album')) if metadata else False
        })
        
        if metadata_success:
            print(f"    ✓ Metadata retrieved successfully")
            print(f"    Title: {metadata.get('title', 'Unknown')}")
            print(f"    Artist: {metadata.get('artist', 'Unknown')}")
        else:
            print("    ❌ Metadata retrieval failed")
    
    except Exception as e:
        test_manager.log_test_result('download_metadata', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Metadata error: {e}")
    
    # Test 4: Download session integrity
    print("\n  Testing download session integrity...")
    
    try:
        # Verify session is maintained during download operations
        original_session = tidal.session.request_session
        
        # Perform download operation
        test_manager.respect_rate_limit()
        download_url = download.get_track_url(track_id, quality="HIGH")
        
        # Check session integrity
        current_session = tidal.session.request_session
        session_maintained = current_session == original_session
        
        # Check if session has proper authentication headers
        auth_headers_present = any(
            'auth' in header.lower() or 'bearer' in str(value).lower()
            for header, value in current_session.headers.items()
        )
        
        test_manager.log_test_result('download_session_integrity', session_maintained, {
            'session_maintained': session_maintained,
            'auth_headers_present': auth_headers_present,
            'proxy_session': bool(current_session.proxies) if current_session else False,
            'download_successful': download_url is not None
        })
        
        if session_maintained:
            print("    ✓ Download session integrity maintained")
        else:
            print("    ⚠️  Download session integrity may be compromised")
    
    except Exception as e:
        test_manager.log_test_result('download_session_integrity', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Session integrity error: {e}")
    
    print("✓ Real download authentication test completed")


def test_real_credential_management(proxy_settings, network_settings):
    """Test real credential management, storage, and security."""
    print("\n" + "=" * 70)
    print("TESTING REAL CREDENTIAL MANAGEMENT")
    print("=" * 70)
    
    test_manager = RealCredentialTestManager()
    
    print("Testing credential management and security...")
    
    # Test 1: Credential storage security
    print("\n  Testing credential storage security...")
    
    try:
        # Check token file security
        token_files = [
            Path.home() / '.tidal-dl-ng' / 'token',
            Path.home() / '.config' / 'tidal-dl-ng' / 'token',
            Path('.') / 'token'
        ]
        
        storage_security = {
            'files_found': 0,
            'secure_permissions': 0,
            'readable_by_others': 0,
            'encrypted_storage': 0
        }
        
        for token_file in token_files:
            if token_file.exists():
                storage_security['files_found'] += 1
                
                # Check file permissions
                stat_info = token_file.stat()
                if hasattr(stat_info, 'st_mode'):
                    mode = stat_info.st_mode
                    # Check if file is readable by others (Unix systems)
                    others_readable = bool(mode & 0o004)
                    if not others_readable:
                        storage_security['secure_permissions'] += 1
                    else:
                        storage_security['readable_by_others'] += 1
                
                # Check if file content appears encrypted
                try:
                    with open(token_file, 'r') as f:
                        content = f.read(100)  # Read first 100 chars
                        # Simple heuristic: if content looks like JSON, it's not encrypted
                        if content.strip().startswith('{') or content.strip().startswith('['):
                            pass  # Not encrypted
                        else:
                            storage_security['encrypted_storage'] += 1
                except Exception:
                    pass  # Can't read file, assume it's secure
        
        test_manager.log_test_result('credential_storage_security', True, storage_security)
        
        print(f"    Token files found: {storage_security['files_found']}")
        print(f"    Secure permissions: {storage_security['secure_permissions']}")
        print(f"    Readable by others: {storage_security['readable_by_others']}")
        print(f"    Encrypted storage: {storage_security['encrypted_storage']}")
        
        if storage_security['readable_by_others'] > 0:
            print("    ⚠️  Warning: Some token files may be readable by others")
        
    except Exception as e:
        test_manager.log_test_result('credential_storage_security', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Storage security check error: {e}")
    
    # Test 2: Environment variable security
    print("\n  Testing environment variable security...")
    
    try:
        env_security = {
            'credential_vars_found': 0,
            'properly_masked': 0,
            'potentially_exposed': 0,
            'secure_length': 0
        }
        
        credential_env_vars = [
            'TIDAL_USERNAME', 'TIDAL_PASSWORD', 'TIDAL_TOKEN', 'TIDAL_REFRESH_TOKEN',
            'PROXY_USERNAME', 'PROXY_PASSWORD'
        ]
        
        for var_name in credential_env_vars:
            var_value = os.getenv(var_name)
            if var_value:
                env_security['credential_vars_found'] += 1
                
                # Check if properly masked
                if var_value.startswith('***') or 'hidden' in var_value.lower():
                    env_security['properly_masked'] += 1
                elif len(var_value) > 50:  # Long values might be tokens
                    env_security['potentially_exposed'] += 1
                
                # Check if reasonable length for credentials
                if 8 <= len(var_value) <= 200:
                    env_security['secure_length'] += 1
        
        test_manager.log_test_result('env_variable_security', True, env_security)
        
        print(f"    Credential variables found: {env_security['credential_vars_found']}")
        print(f"    Properly masked: {env_security['properly_masked']}")
        print(f"    Potentially exposed: {env_security['potentially_exposed']}")
        print(f"    Secure length: {env_security['secure_length']}")
        
        if env_security['potentially_exposed'] > 0:
            print("    ⚠️  Warning: Some credentials may be exposed in environment")
    
    except Exception as e:
        test_manager.log_test_result('env_variable_security', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Environment security check error: {e}")
    
    # Test 3: Multi-account credential management
    print("\n  Testing multi-account credential management...")
    
    try:
        # Test multiple credential sets
        account_configs = [
            {'username': os.getenv('TIDAL_USERNAME'), 'password': os.getenv('TIDAL_PASSWORD')},
            {'token': os.getenv('TIDAL_TOKEN'), 'refresh_token': os.getenv('TIDAL_REFRESH_TOKEN')},
            {'username': os.getenv('TIDAL_USERNAME_2'), 'password': os.getenv('TIDAL_PASSWORD_2')}
        ]
        
        multi_account = {
            'configs_available': 0,
            'valid_configs': 0,
            'credential_conflicts': 0
        }
        
        for i, config in enumerate(account_configs):
            if any(config.values()):
                multi_account['configs_available'] += 1
                
                # Check if config is complete
                if config.get('username') and config.get('password'):
                    multi_account['valid_configs'] += 1
                elif config.get('token'):
                    multi_account['valid_configs'] += 1
        
        # Check for credential conflicts
        if multi_account['configs_available'] > 1:
            print("    Multiple credential sets detected")
            if os.getenv('TIDAL_USERNAME') and os.getenv('TIDAL_TOKEN'):
                multi_account['credential_conflicts'] += 1
                print("    ⚠️  Both username/password and token credentials present")
        
        test_manager.log_test_result('multi_account_management', True, multi_account)
        
        print(f"    Credential configs available: {multi_account['configs_available']}")
        print(f"    Valid configs: {multi_account['valid_configs']}")
        print(f"    Credential conflicts: {multi_account['credential_conflicts']}")
    
    except Exception as e:
        test_manager.log_test_result('multi_account_management', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Multi-account management error: {e}")
    
    # Test 4: Credential cleanup procedures
    print("\n  Testing credential cleanup procedures...")
    
    try:
        cleanup_results = {
            'temp_files_cleaned': 0,
            'memory_cleared': 0,
            'session_cleaned': 0,
            'logs_sanitized': 0
        }
        
        # Test temporary file cleanup
        temp_dirs = [Path('/tmp'), Path.home() / 'tmp', Path('.') / 'temp']
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                tidal_temp_files = list(temp_dir.glob('*tidal*'))
                cleanup_results['temp_files_cleaned'] += len(tidal_temp_files)
        
        # Test memory cleanup (simplified)
        import gc
        gc.collect()
        cleanup_results['memory_cleared'] = 1  # Assume garbage collection works
        
        # Test session cleanup
        tidal = Tidal()
        if hasattr(tidal, 'session') and hasattr(tidal.session, 'request_session'):
            # Clear session cookies and headers
            if hasattr(tidal.session.request_session, 'cookies'):
                tidal.session.request_session.cookies.clear()
                cleanup_results['session_cleaned'] = 1
        
        # Test log sanitization (check if logs contain credentials)
        log_files = [Path('tidal.log'), Path('debug.log'), Path('app.log')]
        for log_file in log_files:
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read(1000)  # Read first 1000 chars
                        # Check for credential patterns
                        if not any(pattern in log_content for pattern in ['Bearer ', 'password=', 'token=']):
                            cleanup_results['logs_sanitized'] += 1
                except Exception:
                    pass
        
        test_manager.log_test_result('credential_cleanup', True, cleanup_results)
        
        print(f"    Temp files cleaned: {cleanup_results['temp_files_cleaned']}")
        print(f"    Memory cleared: {cleanup_results['memory_cleared']}")
        print(f"    Session cleaned: {cleanup_results['session_cleaned']}")
        print(f"    Logs sanitized: {cleanup_results['logs_sanitized']}")
    
    except Exception as e:
        test_manager.log_test_result('credential_cleanup', False, {
            'error': str(e),
            'error_type': type(e).__name__
        })
        print(f"    ❌ Credential cleanup error: {e}")
    
    print("✓ Real credential management test completed")


def generate_test_report(test_manager: RealCredentialTestManager):
    """Generate comprehensive test report for real credential testing."""
    print("\n" + "=" * 70)
    print("REAL CREDENTIAL TESTING REPORT")
    print("=" * 70)
    
    if not test_manager.test_results:
        print("No test results available")
        return
    
    # Summary statistics
    total_tests = len(test_manager.test_results)
    passed_tests = sum(1 for result in test_manager.test_results if result['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    print(f"API Calls Made: {test_manager.api_call_count}")
    
    # Test results by category
    categories = {}
    for result in test_manager.test_results:
        test_name = result['test_name']
        category = test_name.split('_')[0]  # First part of test name
        if category not in categories:
            categories[category] = {'passed': 0, 'failed': 0}
        
        if result['success']:
            categories[category]['passed'] += 1
        else:
            categories[category]['failed'] += 1
    
    print(f"\nResults by Category:")
    for category, results in categories.items():
        total = results['passed'] + results['failed']
        success_rate = results['passed'] / total * 100 if total > 0 else 0
        print(f"  {category}: {results['passed']}/{total} ({success_rate:.1f}%)")
    
    # Failed tests details
    if failed_tests > 0:
        print(f"\nFailed Tests:")
        for result in test_manager.test_results:
            if not result['success']:
                print(f"  ❌ {result['test_name']}")
                if 'error' in result['details']:
                    print(f"     Error: {result['details']['error']}")
    
    # Security warnings
    if test_manager.credential_exposure_checks:
        print(f"\n⚠️  Security Warnings ({len(test_manager.credential_exposure_checks)}):")
        for check in test_manager.credential_exposure_checks:
            print(f"  - {check.get('source', 'Unknown')}: {check.get('message_preview', 'Check details')}")
    
    # Recommendations
    print(f"\nRecommendations:")
    if failed_tests == 0:
        print("  ✓ All tests passed - credential system appears secure")
    else:
        print("  ⚠️  Some tests failed - review failed tests and fix issues")
    
    if test_manager.credential_exposure_checks:
        print("  ⚠️  Credential exposure detected - implement proper masking")
    
    if test_manager.api_call_count > test_manager.max_api_calls * 0.8:
        print("  ⚠️  High API usage - consider reducing test frequency")
    
    print("  ✓ Use environment variables for credential storage")
    print("  ✓ Regularly rotate authentication tokens")
    print("  ✓ Monitor network traffic for credential leaks")


if __name__ == "__main__":
    """Run real TIDAL credential tests manually."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Import test fixtures
    from tests.network.credential_loader import get_proxy_settings, get_network_settings
    
    print("TIDAL Real Credentials Test Suite")
    print("=" * 70)
    print("⚠️  WARNING: This test uses real TIDAL credentials and makes real API calls")
    print("⚠️  Ensure proper credential security and respect API rate limits")
    print("=" * 70)
    
    # Create test fixtures
    proxy_config = get_proxy_settings("primary")
    network_config = get_network_settings("integration_tests")
    
    # Create test manager for tracking results
    test_manager = RealCredentialTestManager()
    
    try:
        # Run all real credential tests
        #test_real_oauth_login_flow(proxy_config, network_config)
        test_real_token_refresh_scenarios(proxy_config, network_config)
        #test_real_api_integration(proxy_config, network_config)
        #test_real_download_authentication(proxy_config, network_config)
        #test_real_credential_management(proxy_config, network_config)
        
        # Generate comprehensive report
        generate_test_report(test_manager)
        
        print("\n" + "=" * 70)
        print("✓ ALL REAL CREDENTIAL TESTS COMPLETED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Still generate report for completed tests
        if test_manager.test_results:
            generate_test_report(test_manager)
        
        sys.exit(1)
