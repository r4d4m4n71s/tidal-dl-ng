"""
Authentication module for TIDAL Downloader Next Generation

This module provides a clean, SOLID-principle based authentication system
with automatic proxy detection and transparent configuration.
"""

from .authentication_manager import AuthenticationManager
from .session_factory import TidalSessionFactory

__all__ = ['AuthenticationManager', 'TidalSessionFactory']
