"""
OAuth authentication strategy with transparent proxy support

Handles OAuth authentication with automatic proxy detection and transparent configuration.
"""

import logging
from typing import TYPE_CHECKING

from .base import AuthenticationStrategy

if TYPE_CHECKING:
    from tidal_dl_ng.enhanced_session import EnhancedTidalSession

logger = logging.getLogger(__name__)


class OAuthAuthStrategy(AuthenticationStrategy):
    """
    OAuth authentication strategy with transparent proxy support.
    
    Automatically detects if proxy is configured and uses the appropriate
    OAuth method (proxy-enhanced or direct) transparently.
    """
    
    @property
    def name(self) -> str:
        """Return the human-readable name of this authentication strategy."""
        return "OAuth Authentication"
    
    @property
    def priority(self) -> int:
        """Return the priority (lower = higher priority)."""
        return 2  # Second priority after token refresh
    
    def authenticate(self, session: 'EnhancedTidalSession') -> bool:
        """
        Perform OAuth authentication with transparent proxy detection.
        
        Args:
            session: The TIDAL session to authenticate
            
        Returns:
            True if authentication was successful, False otherwise
        """
        self._log_attempt()
        
        try:
            # Transparent proxy detection - use proxy-enhanced method if proxy is configured
            if session.proxy_manager:
                logger.info("Proxy configuration detected - using proxy-enhanced OAuth")
                session.login_oauth_simple_with_proxy(fn_print=self._log_oauth_message)
            else:
                logger.info("No proxy configuration - using direct OAuth")
                session.login_oauth_simple(fn_print=self._log_oauth_message)
            
            # Verify authentication was successful
            if session.check_login():
                self._log_success()
                return True
            else:
                self._log_failure()
                return False
                
        except Exception as e:
            self._log_failure(e)
            return False
    
    def _log_oauth_message(self, message: str) -> None:
        """
        Log OAuth messages from the authentication process.
        
        Args:
            message: The message to log
        """
        # Filter and format OAuth messages for better logging
        if "Visit https://" in message:
            logger.info(f"🔗 {message}")
        elif "code will expire" in message:
            logger.info(f"⏰ {message}")
        else:
            logger.debug(f"OAuth: {message}")
