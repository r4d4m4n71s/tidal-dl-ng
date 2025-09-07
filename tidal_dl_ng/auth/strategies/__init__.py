"""
Authentication strategies module

Contains all authentication strategy implementations following the Strategy pattern.
"""

from .base import AuthenticationStrategy
from .token_auth import TokenAuthStrategy
from .oauth_auth import OAuthAuthStrategy
from .device_linking import DeviceLinkingStrategy

__all__ = [
    'AuthenticationStrategy',
    'TokenAuthStrategy', 
    'OAuthAuthStrategy',
    'DeviceLinkingStrategy'
]
