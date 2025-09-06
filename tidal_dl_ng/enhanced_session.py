#!/usr/bin/env python3
"""
Enhanced TIDAL Session with Proxy Integration

This module provides a proxy-aware wrapper around the standard tidalapi.Session
that integrates seamlessly with the existing ProxyManager system.
"""

import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime

import tidalapi
from tidalapi import Session, Config
from tidalapi.session import LinkLogin

from .proxy import ProxyManager
from .model.cfg import Settings

log = logging.getLogger(__name__)


class EnhancedTidalSession(Session):
    """Enhanced TIDAL session with integrated proxy support.
    
    This class extends the standard tidalapi.Session to provide seamless
    proxy integration using the existing ProxyManager system.
    """
    
    def __init__(self, config: Config = Config(), proxy_manager: Optional[ProxyManager] = None):
        """Initialize the proxy-enhanced TIDAL session.
        
        :param config: TIDAL configuration object
        :param proxy_manager: ProxyManager instance for handling proxy operations
        """
        super().__init__(config)
        self.proxy_manager = proxy_manager
        self._original_request_session = self.request_session
        
        # Replace the standard request session with proxy-aware one if proxy manager is available
        if proxy_manager:
            log.info("Initializing TIDAL session with proxy support")
            self.request_session = proxy_manager.create_tidal_session()
            log.info("Proxy-aware request session configured")
        else:
            log.info("Initializing TIDAL session without proxy support")
    
    def get_proxy_status(self) -> Dict[str, Any]:
        """Get current proxy status information.
        
        :return: Dictionary containing proxy status and location information
        """
        if not self.proxy_manager:
            return {
                "enabled": False,
                "proxy_count": 0,
                "active_proxy": None,
                "location_masking": False
            }
        
        # Delegate to the proxy manager's get_proxy_status method
        return self.proxy_manager.get_proxy_status()
    
    def test_proxy_connectivity(self) -> Dict[str, tuple]:
        """Test connectivity of all configured proxies.
        
        :return: Dictionary mapping proxy names to (success, latency, error) tuples
        """
        if not self.proxy_manager:
            return {}
        
        # Delegate to the proxy manager's test_proxy_connectivity method
        return self.proxy_manager.test_proxy_connectivity()
    
    def login_oauth_simple_with_proxy(self, fn_print=print) -> None:
        """Login to TIDAL using OAuth with proxy support.
        
        This method performs OAuth login through the configured proxy,
        with location masking validation.
        
        :param fn_print: Function to display login information
        """
        if not self.proxy_manager:
            log.warning("No proxy manager configured, falling back to standard OAuth login")
            return super().login_oauth_simple(fn_print=fn_print)
        
        # Validate proxy connectivity before attempting login
        log.info("Validating proxy connectivity before OAuth login...")
        connectivity_results = self.test_proxy_connectivity()
        
        successful_proxies = [name for name, (success, _, _) in connectivity_results.items() if success]
        
        if not successful_proxies:
            raise Exception("No working proxies available for OAuth login")
        
        log.info(f"Using proxy for OAuth login: {successful_proxies[0]}")
        
        # Validate location masking
        try:
            proxy_status = self.get_proxy_status()
            if proxy_status.get("location_masking"):
                location_info = proxy_status.get("location_info", {})
                log.info(f"Location masking active - IP: {location_info.get('ip', 'Unknown')}, "
                        f"Country: {location_info.get('country', 'Unknown')}")
            else:
                log.warning("Location masking validation failed")
        except Exception as e:
            log.warning(f"Could not validate location masking: {e}")
        
        # Enhanced print function that includes proxy information
        def proxy_aware_print(message: str) -> None:
            if "Visit https://" in message:
                proxy_info = f" (via proxy: {successful_proxies[0]})"
                fn_print(f"{message}{proxy_info}")
            else:
                fn_print(message)
        
        # Perform OAuth login - the proxy-aware request session will handle all requests
        log.info("Starting OAuth login through proxy...")
        super().login_oauth_simple(fn_print=proxy_aware_print)
        
        # Validate login success
        if self.check_login():
            log.info("✅ OAuth login successful through proxy")
            log.info(f"Session ID: {self.session_id}")
            log.info(f"Country Code: {self.country_code}")
            if self.user:
                log.info(f"User ID: {self.user.id}")
        else:
            log.error("❌ OAuth login failed")
    
    def login_pkce_with_proxy(self, fn_print=print) -> None:
        """Login to TIDAL using PKCE with proxy support.
        
        :param fn_print: Function to display login instructions
        """
        if not self.proxy_manager:
            log.warning("No proxy manager configured, falling back to standard PKCE login")
            return super().login_pkce(fn_print=fn_print)
        
        # Validate proxy connectivity
        connectivity_results = self.test_proxy_connectivity()
        successful_proxies = [name for name, (success, _, _) in connectivity_results.items() if success]
        
        if not successful_proxies:
            raise Exception("No working proxies available for PKCE login")
        
        log.info(f"Using proxy for PKCE login: {successful_proxies[0]}")
        
        # Enhanced print function
        def proxy_aware_print(message: str) -> None:
            if "READ CAREFULLY!" in message or "You need to open this link" in message:
                fn_print(f"{message} [VIA PROXY: {successful_proxies[0]}]")
            else:
                fn_print(message)
        
        # Perform PKCE login through proxy
        log.info("Starting PKCE login through proxy...")
        super().login_pkce(fn_print=proxy_aware_print)
        
        if self.check_login():
            log.info("✅ PKCE login successful through proxy")
        else:
            log.error("❌ PKCE login failed")
    
    def refresh_token_with_proxy_validation(self, refresh_token: str) -> bool:
        """Refresh access token with proxy validation.
        
        :param refresh_token: The refresh token to use
        :return: True if refresh was successful
        """
        if self.proxy_manager:
            # Validate proxy is still working before token refresh
            connectivity_results = self.test_proxy_connectivity()
            working_proxies = [name for name, (success, _, _) in connectivity_results.items() if success]
            
            if not working_proxies:
                log.warning("No working proxies available for token refresh")
                # Could potentially fall back to direct connection here
        
        return super().token_refresh(refresh_token)
    
    def disable_proxy(self) -> None:
        """Disable proxy and revert to direct connection.
        
        This can be useful for debugging or fallback scenarios.
        """
        if self._original_request_session:
            log.info("Disabling proxy, reverting to direct connection")
            self.request_session = self._original_request_session
            self.proxy_manager = None
        else:
            log.warning("No original request session available to revert to")
    
    def enable_proxy(self, proxy_manager: ProxyManager) -> None:
        """Enable proxy support with the given proxy manager.
        
        :param proxy_manager: ProxyManager instance to use
        """
        log.info("Enabling proxy support")
        self.proxy_manager = proxy_manager
        self.request_session = proxy_manager.create_tidal_session()
        log.info("Proxy-aware request session configured")


def create_enhanced_tidal_session(
    settings: Settings,
    quality: Optional[str] = None,
    video_quality: Optional[str] = None
) -> EnhancedTidalSession:
    """Factory function to create an enhanced TIDAL session.
    
    :param settings: Application settings containing proxy configuration
    :param quality: Audio quality override
    :param video_quality: Video quality override
    :return: EnhancedTidalSession instance
    """
    # Create TIDAL configuration
    tidal_config = Config(
        quality=quality or settings.data.quality_audio,
        video_quality=video_quality or settings.data.quality_video,
        item_limit=1000  # Default item limit
    )
    
    # Create proxy manager if proxy settings are enabled
    proxy_manager = None
    if settings.data.proxy_settings.enabled and settings.data.proxy_settings.proxies:
        from .proxy import ProxyManager
        proxy_manager = ProxyManager(settings.data.proxy_settings)
        log.info(f"Created proxy manager with {len(settings.data.proxy_settings.proxies)} proxies")
    else:
        log.info("Proxy settings disabled or no proxies configured")
    
    # Create and return enhanced session
    session = EnhancedTidalSession(tidal_config, proxy_manager)
    
    log.info("Enhanced TIDAL session created successfully")
    return session
