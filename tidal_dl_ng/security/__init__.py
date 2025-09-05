"""
Security module for tidal-dl-ng.

This module provides security enhancements including:
- Secure key management
- Request obfuscation
- Header randomization
- Enhanced download patterns
- Metadata obfuscation
"""

from .key_manager import SecureKeyManager
from .request_obfuscator import RequestObfuscator
from .header_manager import HeaderManager
from .metadata_obfuscator import MetadataObfuscator

__all__ = [
    "SecureKeyManager",
    "RequestObfuscator", 
    "HeaderManager",
    "MetadataObfuscator",
]
