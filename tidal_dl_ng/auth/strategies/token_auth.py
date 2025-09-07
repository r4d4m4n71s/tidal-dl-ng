"""
Token-based authentication strategy

Handles authentication using existing refresh tokens.
"""

import logging
from typing import TYPE_CHECKING

from .base import AuthenticationStrategy

if TYPE_CHECKING:
    from tidal_dl_ng.enhanced_session import EnhancedTidalSession

logger = logging.getLogger(__name__)


class TokenAuthStrategy(AuthenticationStrategy):
    """
    Authentication strategy using existing refresh tokens.
    
    This is the fastest authentication method and should be tried first
    when a valid refresh token is available.
    """
    
    @property
    def name(self) -> str:
        """Return the human-readable name of this authentication strategy."""
        return "Token Refresh"
    
    @property
    def priority(self) -> int:
        """Return the priority (lower = higher priority)."""
        return 1  # Highest priority - try tokens first
    
    def can_authenticate(self, session: 'EnhancedTidalSession') -> bool:
        """
        Check if token authentication is possible.
        
        Args:
            session: The TIDAL session to check
            
        Returns:
            True if a refresh token is available, False otherwise
        """
        return bool(session.refresh_token)
    
    def authenticate(self, session: 'EnhancedTidalSession') -> bool:
        """
        Perform token-based authentication.
        
        Args:
            session: The TIDAL session to authenticate
            
        Returns:
            True if authentication was successful, False otherwise
        """
        if not self.can_authenticate(session):
            logger.debug("No refresh token available for token authentication")
            return False
        
        self._log_attempt()
        
        try:
            # Attempt to refresh the token
            success = session.token_refresh(session.refresh_token)
            
            if success and session.check_login():
                self._log_success()
                return True
            else:
                self._log_failure()
                return False
                
        except Exception as e:
            self._log_failure(e)
            return False
