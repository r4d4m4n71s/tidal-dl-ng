#!/usr/bin/env python3
"""
TIDAL Proxy Integration Bridge

This module provides integration utilities and factory functions to seamlessly
connect the existing TIDAL-DL-NG codebase with the enhanced proxy-aware TIDAL session.
"""

import logging
from typing import Optional, Dict, Any, Callable
from pathlib import Path

import tidalapi
from tidalapi import Session, Config, Quality
from tidalapi.session import LinkLogin

from .enhanced_session import EnhancedTidalSession, create_enhanced_tidal_session
from .model.cfg import Settings
from .proxy import ProxyManager

log = logging.getLogger(__name__)


class TidalProxyIntegration:
    """Main integration class that provides a unified interface for TIDAL operations with proxy support."""
    
    def __init__(self, settings: Settings):
        """Initialize the TIDAL proxy integration.
        
        :param settings: Application settings containing proxy and TIDAL configuration
        """
        self.settings = settings
        self.session: Optional[EnhancedTidalSession] = None
        self._session_file: Optional[Path] = None
    
    def create_session(
        self,
        quality: Optional[str] = None,
        video_quality: Optional[str] = None
    ) -> EnhancedTidalSession:
        """Create a new enhanced TIDAL session.
        
        :param quality: Audio quality override
        :param video_quality: Video quality override
        :return: EnhancedTidalSession instance
        """
        log.info("Creating new TIDAL session with proxy integration")
        
        self.session = create_enhanced_tidal_session(
            settings=self.settings,
            quality=quality,
            video_quality=video_quality
        )
        
        return self.session
    
    def get_session(self) -> EnhancedTidalSession:
        """Get the current session, creating one if it doesn't exist.
        
        :return: Current EnhancedTidalSession instance
        """
        if self.session is None:
            self.session = self.create_session()
        
        return self.session
    
    def login_oauth(self, fn_print: Callable[[str], None] = print) -> bool:
        """Perform OAuth login with proxy support.
        
        :param fn_print: Function to display login information
        :return: True if login was successful
        """
        session = self.get_session()
        
        try:
            if session.proxy_manager:
                log.info("Performing OAuth login through proxy")
                session.login_oauth_simple_with_proxy(fn_print=fn_print)
            else:
                log.info("Performing standard OAuth login (no proxy)")
                session.login_oauth_simple(fn_print=fn_print)
            
            success = session.check_login()
            if success:
                log.info("✅ OAuth login successful")
                self._log_session_info()
            else:
                log.error("❌ OAuth login failed")
            
            return success
            
        except Exception as e:
            log.error(f"OAuth login failed with exception: {e}")
            return False
    
    def login_pkce(self, fn_print: Callable[[str], None] = print) -> bool:
        """Perform PKCE login with proxy support.
        
        :param fn_print: Function to display login instructions
        :return: True if login was successful
        """
        session = self.get_session()
        
        try:
            if session.proxy_manager:
                log.info("Performing PKCE login through proxy")
                session.login_pkce_with_proxy(fn_print=fn_print)
            else:
                log.info("Performing standard PKCE login (no proxy)")
                session.login_pkce(fn_print=fn_print)
            
            success = session.check_login()
            if success:
                log.info("✅ PKCE login successful")
                self._log_session_info()
            else:
                log.error("❌ PKCE login failed")
            
            return success
            
        except Exception as e:
            log.error(f"PKCE login failed with exception: {e}")
            return False
    
    def login_session_file(
        self,
        session_file: Path,
        do_pkce: bool = False,
        fn_print: Callable[[str], None] = print
    ) -> bool:
        """Login using session file with proxy support.
        
        :param session_file: Path to session file
        :param do_pkce: Whether to use PKCE login if session file is invalid
        :param fn_print: Function to display login information
        :return: True if login was successful
        """
        session = self.get_session()
        self._session_file = session_file
        
        try:
            # Try to load existing session
            if session_file.exists():
                log.info(f"Loading session from {session_file}")
                success = session.load_session_from_file(session_file)
                
                if success and session.check_login():
                    log.info("✅ Session loaded successfully from file")
                    self._log_session_info()
                    return True
                else:
                    log.warning("Session file exists but is invalid, creating new session")
            
            # Create new session
            if do_pkce:
                success = self.login_pkce(fn_print=fn_print)
            else:
                success = self.login_oauth(fn_print=fn_print)
            
            # Save session if successful
            if success:
                session.save_session_to_file(session_file)
                log.info(f"Session saved to {session_file}")
            
            return success
            
        except Exception as e:
            log.error(f"Session file login failed: {e}")
            return False
    
    def get_proxy_status(self) -> Dict[str, Any]:
        """Get current proxy status.
        
        :return: Dictionary containing proxy status information
        """
        if self.session:
            return self.session.get_proxy_status()
        else:
            # Return status based on settings even if no session exists
            if self.settings.data.proxy_settings.enabled:
                return {
                    "enabled": True,
                    "proxy_count": len(self.settings.data.proxy_settings.proxies),
                    "active_proxy": None,
                    "location_masking": False,
                    "session_created": False
                }
            else:
                return {
                    "enabled": False,
                    "proxy_count": 0,
                    "active_proxy": None,
                    "location_masking": False,
                    "session_created": False
                }
    
    def test_proxy_connectivity(self) -> Dict[str, tuple]:
        """Test proxy connectivity.
        
        :return: Dictionary mapping proxy names to (success, latency, error) tuples
        """
        session = self.get_session()
        return session.test_proxy_connectivity()
    
    def validate_location_masking(self) -> Optional[Dict[str, Any]]:
        """Validate that location masking is working.
        
        :return: Location information if masking is active, None otherwise
        """
        session = self.get_session()
        if session.proxy_manager:
            try:
                return session.proxy_manager.validate_location_masking()
            except Exception as e:
                log.warning(f"Location masking validation failed: {e}")
                return None
        return None
    
    def disable_proxy(self) -> None:
        """Disable proxy and revert to direct connection."""
        if self.session:
            self.session.disable_proxy()
            log.info("Proxy disabled for current session")
    
    def enable_proxy(self) -> None:
        """Enable proxy support if configured."""
        if self.session and self.settings.data.proxy_settings.enabled:
            proxy_manager = ProxyManager(self.settings.data.proxy_settings)
            self.session.enable_proxy(proxy_manager)
            log.info("Proxy enabled for current session")
    
    def _log_session_info(self) -> None:
        """Log current session information."""
        if self.session:
            log.info(f"Session ID: {self.session.session_id}")
            log.info(f"Country Code: {self.session.country_code}")
            if self.session.user:
                log.info(f"User ID: {self.session.user.id}")
            
            # Log proxy status
            proxy_status = self.session.get_proxy_status()
            if proxy_status.get("enabled"):
                log.info(f"Proxy Status: {proxy_status.get('active_proxy', 'Unknown')} "
                        f"(Location Masking: {'✅' if proxy_status.get('location_masking') else '❌'})")


# Factory functions for backward compatibility and easy integration

def create_tidal_session_with_proxy(settings: Settings) -> EnhancedTidalSession:
    """Create a TIDAL session with proxy support.
    
    This is a simple factory function for backward compatibility.
    
    :param settings: Application settings
    :return: EnhancedTidalSession instance
    """
    return create_enhanced_tidal_session(settings)


def get_tidal_integration(settings: Settings) -> TidalProxyIntegration:
    """Get a TIDAL proxy integration instance.
    
    :param settings: Application settings
    :return: TidalProxyIntegration instance
    """
    return TidalProxyIntegration(settings)


# Utility functions for common operations

def quick_proxy_test(settings: Settings) -> Dict[str, Any]:
    """Quickly test proxy configuration without creating a full session.
    
    :param settings: Application settings
    :return: Dictionary with test results
    """
    if not settings.data.proxy_settings.enabled:
        return {
            "proxy_enabled": False,
            "message": "Proxy settings are disabled"
        }
    
    try:
        proxy_manager = ProxyManager(settings.data.proxy_settings)
        
        # Test basic connectivity
        test_session = proxy_manager.create_session()
        response = test_session.get("https://httpbin.org/ip", timeout=10)
        response.raise_for_status()
        
        ip_info = response.json()
        
        return {
            "proxy_enabled": True,
            "connectivity": True,
            "proxy_ip": ip_info.get("origin", "Unknown"),
            "proxy_count": len(settings.data.proxy_settings.proxies),
            "message": "Proxy connectivity test successful"
        }
        
    except Exception as e:
        return {
            "proxy_enabled": True,
            "connectivity": False,
            "error": str(e),
            "message": "Proxy connectivity test failed"
        }


def migrate_existing_session_to_proxy(
    existing_session: Session,
    settings: Settings
) -> EnhancedTidalSession:
    """Migrate an existing TIDAL session to use proxy support.
    
    This function helps migrate existing code that uses standard tidalapi.Session
    to the enhanced version.
    
    :param existing_session: Existing tidalapi.Session instance
    :param settings: Application settings with proxy configuration
    :return: New EnhancedTidalSession with transferred credentials
    """
    log.info("Migrating existing TIDAL session to proxy-enhanced version")
    
    # Create new proxy-enhanced session
    enhanced_session = create_enhanced_tidal_session(settings)
    
    # Transfer authentication data if available
    if existing_session.access_token:
        enhanced_session.load_oauth_session(
            token_type=existing_session.token_type or "Bearer",
            access_token=existing_session.access_token,
            refresh_token=existing_session.refresh_token,
            expiry_time=existing_session.expiry_time,
            is_pkce=getattr(existing_session, 'is_pkce', False)
        )
        log.info("✅ Authentication data transferred to proxy-enhanced session")
    elif existing_session.session_id:
        enhanced_session.load_session(
            session_id=existing_session.session_id,
            country_code=existing_session.country_code,
            user_id=existing_session.user.id if existing_session.user else None
        )
        log.info("✅ Session data transferred to proxy-enhanced session")
    
    return enhanced_session


# Debug and diagnostic functions

def diagnose_proxy_integration(settings: Settings) -> Dict[str, Any]:
    """Comprehensive diagnostic of proxy integration setup.
    
    :param settings: Application settings
    :return: Diagnostic information
    """
    diagnosis = {
        "proxy_settings": {
            "enabled": settings.data.proxy_settings.enabled,
            "proxy_count": len(settings.data.proxy_settings.proxies),
            "proxies": []
        },
        "connectivity": {},
        "location_masking": {},
        "tidal_integration": {}
    }
    
    # Analyze proxy settings
    for proxy in settings.data.proxy_settings.proxies:
        diagnosis["proxy_settings"]["proxies"].append({
            "name": proxy.name,
            "host": proxy.host,
            "port": proxy.port,
            "type": proxy.proxy_type,
            "enabled": proxy.enabled,
            "protocols": proxy.protocols
        })
    
    # Test connectivity if proxies are enabled
    if settings.data.proxy_settings.enabled:
        try:
            integration = TidalProxyIntegration(settings)
            diagnosis["connectivity"] = integration.test_proxy_connectivity()
            
            # Test location masking
            location_info = integration.validate_location_masking()
            if location_info:
                diagnosis["location_masking"] = {
                    "active": True,
                    "info": location_info
                }
            else:
                diagnosis["location_masking"] = {
                    "active": False,
                    "error": "Could not validate location masking"
                }
                
        except Exception as e:
            diagnosis["connectivity"]["error"] = str(e)
    
    # Test TIDAL integration
    try:
        session = create_enhanced_tidal_session(settings)
        diagnosis["tidal_integration"] = {
            "session_created": True,
            "proxy_manager_available": session.proxy_manager is not None,
            "proxy_status": session.get_proxy_status()
        }
    except Exception as e:
        diagnosis["tidal_integration"] = {
            "session_created": False,
            "error": str(e)
        }
    
    return diagnosis
