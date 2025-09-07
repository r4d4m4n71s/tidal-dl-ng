"""
Device linking authentication strategy

Fallback authentication method using TIDAL's device linking system.
"""

import logging
import sys
from typing import TYPE_CHECKING

from .base import AuthenticationStrategy

if TYPE_CHECKING:
    from tidal_dl_ng.enhanced_session import EnhancedTidalSession

logger = logging.getLogger(__name__)


class DeviceLinkingStrategy(AuthenticationStrategy):
    """
    Device linking authentication strategy.
    
    This is a fallback authentication method that uses TIDAL's device linking
    system when other methods fail. It provides a user-friendly dialog-based
    authentication flow.
    """
    
    @property
    def name(self) -> str:
        """Return the human-readable name of this authentication strategy."""
        return "Device Linking"
    
    @property
    def priority(self) -> int:
        """Return the priority (lower = higher priority)."""
        return 3  # Lowest priority - fallback method
    
    def authenticate(self, session: 'EnhancedTidalSession') -> bool:
        """
        Perform device linking authentication.
        
        Args:
            session: The TIDAL session to authenticate
            
        Returns:
            True if authentication was successful, False otherwise
        """
        self._log_attempt()
        
        try:
            # Import here to avoid circular imports
            from tidal_dl_ng.dialog import DialogLogin
            from requests.exceptions import HTTPError
            from tidalapi.session import LinkLogin
            
            hint = "After you have finished the TIDAL login via web browser click the 'OK' button."
            
            while True:
                try:
                    # Get device linking information
                    link_login: LinkLogin = session.get_link_login()
                    
                    # Show login dialog
                    d_login = DialogLogin(
                        url_login=link_login.verification_uri_complete,
                        hint=hint,
                        expires_in=link_login.expires_in,
                        parent=None,  # No parent since this is a fallback
                    )
                    
                    if d_login.return_code == 1:
                        try:
                            # Process the device linking
                            session.process_link_login(link_login, until_expiry=False)
                            
                            # Verify authentication was successful
                            if session.check_login():
                                self._log_success()
                                return True
                            else:
                                self._log_failure()
                                return False
                                
                        except (HTTPError, Exception) as e:
                            hint = "Something was wrong with your redirect url. Please try again!"
                            logger.warning(f"Device linking failed: {str(e)}. Retrying...")
                            continue
                    else:
                        # User cancelled authentication
                        logger.warning("Device linking authentication cancelled by user.")
                        return False
                        
                except Exception as e:
                    self._log_failure(e)
                    return False
                    
        except Exception as e:
            self._log_failure(e)
            return False
