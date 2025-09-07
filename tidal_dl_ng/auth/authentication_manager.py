"""
Authentication Manager

Orchestrates TIDAL authentication using the Strategy pattern with SOLID principles.
Provides a single, clean interface for all authentication needs.
"""

import logging
import sys
from typing import TYPE_CHECKING, List, Optional

from .session_factory import TidalSessionFactory
from .strategies import (
    AuthenticationStrategy,
    TokenAuthStrategy,
    OAuthAuthStrategy,
    DeviceLinkingStrategy
)

if TYPE_CHECKING:
    from tidal_dl_ng.enhanced_session import EnhancedTidalSession
    from tidal_dl_ng.model.cfg import Settings
    from tidal_dl_ng.config import Tidal

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """
    Manages TIDAL authentication using the Strategy pattern.
    
    Follows SOLID principles:
    - Single Responsibility: Handles only authentication orchestration
    - Open/Closed: Easy to add new authentication strategies
    - Dependency Inversion: Depends on abstractions (AuthenticationStrategy)
    
    Implements DRY principle by providing a single authentication flow
    that works transparently with or without proxy configuration.
    """
    
    def __init__(self, settings: 'Settings', parent=None):
        """
        Initialize the authentication manager.
        
        Args:
            settings: Application settings
            parent: Parent widget for GUI dialogs (optional)
        """
        self.settings = settings
        self.parent = parent
        self.session_factory = TidalSessionFactory(settings)
        self.session: Optional['EnhancedTidalSession'] = None
        self.tidal: Optional['Tidal'] = None
        
        # Define authentication strategies in priority order (lower number = higher priority)
        self.strategies: List[AuthenticationStrategy] = [
            TokenAuthStrategy(),
            OAuthAuthStrategy(),
            DeviceLinkingStrategy()
        ]
        
        # Sort strategies by priority
        self.strategies.sort(key=lambda s: s.priority)
    
    def authenticate(self) -> bool:
        """
        Perform TIDAL authentication using the best available strategy.
        
        This method implements the DRY principle by providing a single
        authentication flow that works transparently regardless of proxy
        configuration or authentication method.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        logger.info("Starting TIDAL authentication process")
        
        try:
            # Ensure proxy configuration if needed
            if not self._ensure_proxy_configuration():
                logger.error("Proxy configuration failed or was cancelled")
                return False
            
            # Create session with transparent proxy detection
            self.session = self.session_factory.create_session()
            
            # Try each authentication strategy in priority order
            for strategy in self.strategies:
                if not strategy.can_authenticate(self.session):
                    logger.debug(f"Skipping {strategy.name} - requirements not met")
                    continue
                
                try:
                    if strategy.authenticate(self.session):
                        # Authentication successful
                        self._finalize_authentication()
                        logger.info(f"🎉 Authentication completed successfully using {strategy.name}")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Authentication strategy {strategy.name} failed: {str(e)}")
                    continue
            
            # All strategies failed
            logger.error("❌ All authentication strategies failed")
            return False
            
        except Exception as e:
            logger.error(f"Authentication process failed: {str(e)}")
            return False
    
    def get_tidal_instance(self) -> Optional['Tidal']:
        """
        Get the authenticated TIDAL instance.
        
        Returns:
            The authenticated Tidal instance, or None if not authenticated
        """
        return self.tidal
    
    def get_session(self) -> Optional['EnhancedTidalSession']:
        """
        Get the authenticated TIDAL session.
        
        Returns:
            The authenticated session, or None if not authenticated
        """
        return self.session
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return (
            self.session is not None and 
            self.session.check_login() and
            self.tidal is not None
        )
    
    def _ensure_proxy_configuration(self) -> bool:
        """
        Ensure proxy configuration is set up if needed.
        
        Shows proxy configuration dialog only if no proxy is configured
        and user hasn't explicitly chosen to skip proxy configuration.
        
        Returns:
            True if proxy configuration is ready or not needed, False if cancelled
        """
        # Check if proxy configuration already exists
        if self.session_factory.has_proxy_configuration():
            logger.info("Using existing proxy configuration")
            return True
        
        # Check if there are any proxy settings at all (even if disabled)
        if len(self.settings.data.proxy_settings.proxies) > 0:
            logger.info("Proxy configuration exists but is disabled - using direct connection")
            return True
        
        # No proxy configuration exists - show dialog
        logger.info("No proxy configuration found - showing proxy setup dialog")
        
        try:
            # Import here to avoid circular imports
            from tidal_dl_ng.dialog import DialogProxyConfig
            
            proxy_dialog = DialogProxyConfig(self.settings, parent=self.parent)
            
            if proxy_dialog.result_configured:
                logger.info("Proxy configuration completed")
                return True
            elif proxy_dialog.result_skip_proxy:
                logger.info("User chose to skip proxy configuration - using direct connection")
                return True
            else:
                logger.warning("Proxy configuration cancelled by user")
                return False
                
        except Exception as e:
            logger.error(f"Error showing proxy configuration dialog: {str(e)}")
            return False
    
    def _finalize_authentication(self) -> None:
        """
        Finalize the authentication process by creating the Tidal instance.
        """
        if not self.session:
            raise RuntimeError("No session available for finalization")
        
        # Import here to avoid circular imports
        from tidal_dl_ng.config import Tidal
        
        # Create Tidal instance with the authenticated session
        self.tidal = Tidal(self.settings, session=self.session)
        
        # Log authentication details
        if self.session.user:
            logger.info(f"Authenticated as user: {self.session.user.id}")
        if self.session.country_code:
            logger.info(f"Country code: {self.session.country_code}")
        if self.session.session_id:
            logger.debug(f"Session ID: {self.session.session_id}")
