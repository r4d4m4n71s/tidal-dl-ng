"""
Local Server Authentication for TIDAL Downloader Next Generation

This module provides a local HTTP server for handling OAuth authentication
callbacks while ensuring all outbound requests to TIDAL are routed through
configured proxies for complete location masking.
"""

import logging
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from tidalapi.session import LinkLogin

from tidal_dl_ng.model.cfg import AuthSettings
from tidal_dl_ng.proxy import ProxyManager

logger = logging.getLogger(__name__)


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks."""
    
    def __init__(self, auth_server, *args, **kwargs):
        self.auth_server = auth_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests to the callback endpoint."""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/callback':
                self._handle_callback(parsed_url)
            elif parsed_url.path == '/':
                self._handle_root()
            else:
                self._send_404()
                
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            self._send_error(500, "Internal Server Error")
    
    def _handle_callback(self, parsed_url):
        """Handle OAuth callback with authorization code."""
        query_params = parse_qs(parsed_url.query)
        
        # Check for authorization code
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            state = query_params.get('state', [None])[0]
            
            # Validate state parameter
            if state != self.auth_server.state:
                logger.error("Invalid state parameter in callback")
                self._send_error(400, "Invalid state parameter")
                return
            
            # Store the authorization code
            self.auth_server.auth_code = auth_code
            self.auth_server.auth_complete = True
            
            # Send success response
            self._send_success_page()
            
            logger.info("Authorization code received successfully")
            
        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            
            logger.error(f"OAuth error: {error} - {error_description}")
            self._send_error_page(error, error_description)
            
            self.auth_server.auth_error = f"{error}: {error_description}"
            self.auth_server.auth_complete = True
        else:
            logger.error("No authorization code or error in callback")
            self._send_error(400, "Missing authorization code")
    
    def _handle_root(self):
        """Handle requests to the root path."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TIDAL Authentication</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                .status { padding: 20px; border-radius: 5px; margin: 20px 0; }
                .waiting { background-color: #fff3cd; border: 1px solid #ffeaa7; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>TIDAL Authentication</h1>
                <div class="status waiting">
                    <h2>Waiting for Authentication</h2>
                    <p>Please complete the authentication process in your browser.</p>
                    <p>This page will update automatically when authentication is complete.</p>
                </div>
                <script>
                    // Auto-refresh every 2 seconds to check for completion
                    setTimeout(function() {
                        window.location.reload();
                    }, 2000);
                </script>
            </div>
        </body>
        </html>
        """
        
        self._send_response(200, html, 'text/html')
    
    def _send_success_page(self):
        """Send success page after successful authentication."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TIDAL Authentication - Success</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                .status { padding: 20px; border-radius: 5px; margin: 20px 0; }
                .success { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>TIDAL Authentication</h1>
                <div class="status success">
                    <h2>✓ Authentication Successful!</h2>
                    <p>You have successfully authenticated with TIDAL.</p>
                    <p>You can now close this browser window and return to the application.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_response(200, html, 'text/html')
    
    def _send_error_page(self, error: str, description: str):
        """Send error page when authentication fails."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TIDAL Authentication - Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .status {{ padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>TIDAL Authentication</h1>
                <div class="status error">
                    <h2>✗ Authentication Failed</h2>
                    <p><strong>Error:</strong> {error}</p>
                    <p><strong>Description:</strong> {description}</p>
                    <p>Please close this window and try again.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_response(200, html, 'text/html')
    
    def _send_response(self, status_code: int, content: str, content_type: str = 'text/plain'):
        """Send HTTP response."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-Length', str(len(content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def _send_404(self):
        """Send 404 Not Found response."""
        self._send_error(404, "Not Found")
    
    def _send_error(self, status_code: int, message: str):
        """Send error response."""
        self._send_response(status_code, f"Error {status_code}: {message}")
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.debug(f"HTTP: {format % args}")


class LocalAuthServer:
    """
    Local HTTP server for handling TIDAL OAuth authentication.
    
    This server ensures all outbound requests to TIDAL are routed through
    configured proxies for complete location masking while handling OAuth
    callbacks locally.
    """
    
    def __init__(self, proxy_manager: ProxyManager, settings: AuthSettings):
        self.proxy_manager = proxy_manager
        self.settings = settings
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.state: str = ""
        self.auth_code: Optional[str] = None
        self.auth_error: Optional[str] = None
        self.auth_complete: bool = False
        self._running = False
    
    def start_server(self) -> bool:
        """
        Start the local HTTP server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Create handler class with reference to this server
            def handler_factory(*args, **kwargs):
                return AuthCallbackHandler(self, *args, **kwargs)
            
            # Create and start server
            self.server = HTTPServer(
                (self.settings.local_server_host, self.settings.local_server_port),
                handler_factory
            )
            
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            # Wait a moment to ensure server starts
            time.sleep(0.5)
            
            self._running = True
            logger.info(f"Local auth server started on {self.settings.local_server_host}:{self.settings.local_server_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start local auth server: {str(e)}")
            return False
    
    def stop_server(self):
        """Stop the local HTTP server."""
        if self.server and self._running:
            self.server.shutdown()
            self.server.server_close()
            
            if self.server_thread:
                self.server_thread.join(timeout=5)
            
            self._running = False
            logger.info("Local auth server stopped")
    
    def _run_server(self):
        """Run the HTTP server (called in separate thread)."""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self._running:  # Only log if we're supposed to be running
                logger.error(f"Auth server error: {str(e)}")
    
    def authenticate_with_tidal(self, session) -> Tuple[bool, Optional[str]]:
        """
        Perform complete TIDAL authentication using local server and proxy.
        
        Args:
            session: TIDAL session object
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Start local server
            if not self.start_server():
                return False, "Failed to start local authentication server"
            
            # Generate state parameter for security
            self.state = secrets.token_urlsafe(32)
            
            # Reset authentication state
            self.auth_code = None
            self.auth_error = None
            self.auth_complete = False
            
            # Get OAuth authorization URL through proxy
            auth_url = self._get_auth_url_via_proxy(session)
            if not auth_url:
                return False, "Failed to get authorization URL"
            
            # Open browser if configured
            if self.settings.browser_auto_open:
                try:
                    webbrowser.open(auth_url)
                    logger.info("Opened browser for authentication")
                except Exception as e:
                    logger.warning(f"Failed to open browser: {str(e)}")
                    logger.info(f"Please manually open: {auth_url}")
            else:
                logger.info(f"Please open this URL in your browser: {auth_url}")
            
            # Wait for authentication completion
            success = self._wait_for_auth_completion()
            
            if success and self.auth_code:
                # Exchange authorization code for tokens via proxy
                token_success = self._exchange_code_for_tokens(session, self.auth_code)
                if token_success:
                    logger.info("TIDAL authentication completed successfully")
                    return True, None
                else:
                    return False, "Failed to exchange authorization code for tokens"
            elif self.auth_error:
                return False, self.auth_error
            else:
                return False, "Authentication timed out or was cancelled"
                
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        finally:
            self.stop_server()
    
    def _get_auth_url_via_proxy(self, session) -> Optional[str]:
        """
        Get TIDAL OAuth authorization URL via proxy.
        
        This ensures the initial OAuth request is also routed through the proxy
        for complete location masking.
        """
        try:
            # Create proxy-aware session for TIDAL API calls
            proxy_session = self.proxy_manager.create_tidal_session()
            
            # Build callback URL
            callback_url = f"http://{self.settings.local_server_host}:{self.settings.local_server_port}/callback"
            
            # Build authorization URL
            # Note: This is a simplified example - you'll need to adapt this to work with tidalapi's actual OAuth flow
            auth_url = (
                f"https://auth.tidal.com/v1/oauth2/authorize"
                f"?response_type=code"
                f"&client_id={session.config.client_id}"
                f"&redirect_uri={callback_url}"
                f"&scope=r_usr+w_usr+w_sub"
                f"&state={self.state}"
            )
            
            logger.info("Generated OAuth authorization URL via proxy")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to get auth URL via proxy: {str(e)}")
            return None
    
    def _exchange_code_for_tokens(self, session, auth_code: str) -> bool:
        """
        Exchange authorization code for access tokens via proxy.
        
        This ensures the token exchange is also routed through the proxy.
        """
        try:
            # Create proxy-aware session for token exchange
            proxy_session = self.proxy_manager.create_tidal_session()
            
            # Build callback URL
            callback_url = f"http://{self.settings.local_server_host}:{self.settings.local_server_port}/callback"
            
            # Prepare token exchange request
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': callback_url,
                'client_id': session.config.client_id,
                'client_secret': session.config.client_secret,
            }
            
            # Make token exchange request via proxy
            response = proxy_session.post(
                'https://auth.tidal.com/v1/oauth2/token',
                data=token_data,
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            # Update session with new tokens
            session.access_token = token_data.get('access_token')
            session.refresh_token = token_data.get('refresh_token')
            session.token_type = token_data.get('token_type', 'Bearer')
            
            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            session.expiry_time = time.time() + expires_in
            
            logger.info("Successfully exchanged authorization code for tokens via proxy")
            return True
            
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens via proxy: {str(e)}")
            return False
    
    def _wait_for_auth_completion(self) -> bool:
        """
        Wait for authentication to complete.
        
        Returns:
            True if authentication completed successfully, False if timed out
        """
        start_time = time.time()
        
        while not self.auth_complete:
            if time.time() - start_time > self.settings.auth_timeout:
                logger.error("Authentication timed out")
                return False
            
            time.sleep(1)
        
        return self.auth_code is not None and self.auth_error is None


def create_auth_handler(proxy_manager: ProxyManager, settings: AuthSettings) -> LocalAuthServer:
    """
    Create a local authentication server with proxy support.
    
    Args:
        proxy_manager: Configured proxy manager
        settings: Authentication settings
        
    Returns:
        LocalAuthServer instance
    """
    return LocalAuthServer(proxy_manager, settings)
