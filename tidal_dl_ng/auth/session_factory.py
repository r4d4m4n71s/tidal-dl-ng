"""
TIDAL Session Factory

Creates TIDAL sessions with automatic proxy detection and transparent configuration.
Follows the Factory pattern and Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tidal_dl_ng.enhanced_session import EnhancedTidalSession
    from tidal_dl_ng.model.cfg import Settings

logger = logging.getLogger(__name__)


class TidalSessionFactory:
    """
    Factory for creating TIDAL sessions with transparent proxy configuration.
    
    Handles the complexity of session creation and proxy detection,
    following the Single Responsibility Principle.
    """
    
    def __init__(self, settings: 'Settings'):
        """
        Initialize the session factory.
        
        Args:
            settings: Application settings containing proxy configuration
        """
        self.settings = settings
    
    def create_session(self) -> 'EnhancedTidalSession':
        """
        Create an enhanced TIDAL session with automatic proxy detection.
        
        This method transparently detects proxy configuration from settings
        and creates the appropriate session type without requiring the caller
        to know about proxy details.
        
        Returns:
            An EnhancedTidalSession with proxy support if configured
        """
        logger.debug("Creating TIDAL session with automatic proxy detection")
        
        # Import here to avoid circular imports
        from tidal_dl_ng.enhanced_session import create_enhanced_tidal_session
        
        # The enhanced session factory already handles proxy detection transparently
        session = create_enhanced_tidal_session(self.settings)
        
        # Log the session configuration for debugging
        if session.proxy_manager:
            proxy_status = session.get_proxy_status()
            logger.info(f"Created TIDAL session with proxy support: {proxy_status.get('proxy_name', 'Unknown')}")
        else:
            logger.info("Created TIDAL session with direct connection")
        
        return session
    
    def has_proxy_configuration(self) -> bool:
        """
        Check if proxy configuration exists in settings.
        
        Returns:
            True if proxy is configured and enabled, False otherwise
        """
        proxy_settings = self.settings.data.proxy_settings
        return (
            proxy_settings.enabled and 
            len(proxy_settings.proxies) > 0
        )
    
    def get_proxy_info(self) -> dict:
        """
        Get information about the current proxy configuration.
        
        Returns:
            Dictionary containing proxy configuration details
        """
        if not self.has_proxy_configuration():
            return {
                "enabled": False,
                "proxy_count": 0,
                "status": "No proxy configured"
            }
        
        proxy_settings = self.settings.data.proxy_settings
        enabled_proxies = [p for p in proxy_settings.proxies if p.enabled]
        
        return {
            "enabled": True,
            "proxy_count": len(proxy_settings.proxies),
            "enabled_proxy_count": len(enabled_proxies),
            "status": f"{len(enabled_proxies)} proxy(ies) available"
        }
