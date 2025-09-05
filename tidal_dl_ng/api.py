import json
import os
from typing import Dict, List, Any, Optional

import requests

from tidal_dl_ng.constants import REQUESTS_TIMEOUT_SEC
from tidal_dl_ng.security.key_manager import SecureKeyManager
from tidal_dl_ng.security.header_manager import HeaderManager

# Legacy keys for backward compatibility and migration
__LEGACY_KEYS_JSON__ = """
{
    "version": "1.0.1",
    "keys": [
        {
            "platform": "Fire TV",
            "formats": "Normal/High/HiFi(No Master)",
            "clientId": "OmDtrzFgyVVL6uW56OnFA2COiabqm",
            "clientSecret": "zxen1r3pO0hgtOC7j6twMo9UAqngGrmRiWpV7QC1zJ8=",
            "valid": "False",
            "from": "Fokka-Engineering (https://github.com/Fokka-Engineering/libopenTIDAL/blob/655528e26e4f3ee2c426c06ea5b8440cf27abc4a/README.md#example)"
        },
        {
            "platform": "Fire TV",
            "formats": "Master-Only(Else Error)",
            "clientId": "7m7Ap0JC9j1cOM3n",
            "clientSecret": "vRAdA108tlvkJpTsGZS8rGZ7xTlbJ0qaZ2K9saEzsgY=",
            "valid": "True",
            "from": "Dniel97 (https://github.com/Dniel97/RedSea/blob/4ba02b88cee33aeb735725cb854be6c66ff372d4/config/settings.example.py#L68)"
        },
        {
            "platform": "Android TV",
            "formats": "Normal/High/HiFi(No Master)",
            "clientId": "Pzd0ExNVHkyZLiYN",
            "clientSecret": "W7X6UvBaho+XOi1MUeCX6ewv2zTdSOV3Y7qC3p3675I=",
            "valid": "False",
            "from": ""
        },
        {
            "platform": "TV",
            "formats": "Normal/High/HiFi/Master",
            "clientId": "8SEZWa4J1NVC5U5Y",
            "clientSecret": "owUYDkxddz+9FpvGX24DlxECNtFEMBxipU0lBfrbq60=",
            "valid": "False",
            "from": "morguldir (https://github.com/morguldir/python-tidal/commit/50f1afcd2079efb2b4cf694ef5a7d67fdf619d09)"
        },
        {
            "platform": "Android Auto",
            "formats": "Normal/High/HiFi/Master",
            "clientId": "zU4XHVVkc2tDPo4t",
            "clientSecret": "VJKhDFqJPqvsPVNBV6ukXTJmwlvbttP7wlMlrc72se4=",
            "valid": "True",
            "from": "1nikolas (https://github.com/yaronzz/Tidal-Media-Downloader/pull/840)"
        }
    ]
}
"""

__ERROR_KEY__ = {
    "platform": "None",  
    "formats": "",
    "clientId": "",
    "clientSecret": "",
    "valid": "False",
}


class APIKeyProvider:
    """Secure API key provider with rotation and obfuscation."""
    
    def __init__(self):
        """Initialize the API key provider."""
        self.key_manager = SecureKeyManager()
        self.header_manager = HeaderManager()
        self._keys: Optional[List[Dict[str, Any]]] = None
        self._current_key_index = 0
        self._initialize_keys()
        
    def _initialize_keys(self) -> None:
        """Initialize keys from various sources."""
        # Try environment variables first
        env_key = self.key_manager.get_key_from_env()
        if env_key:
            self._keys = [env_key]
            print("Using API keys from environment variables.")
            return
            
        # Try secure storage
        stored_keys = self.key_manager.decrypt_keys()
        if stored_keys:
            self._keys = stored_keys
            print("Using API keys from secure storage.")
            return
            
        # Fallback to legacy mode and migrate
        print("No secure keys found. Performing one-time migration...")
        legacy_keys = json.loads(__LEGACY_KEYS_JSON__)["keys"]
        
        if self.key_manager.migrate_legacy_keys(legacy_keys):
            self._keys = legacy_keys
            print("Successfully migrated keys to secure storage.")
        else:
            print("Warning: Could not migrate keys. Using legacy mode.")
            self._keys = legacy_keys
            
        # Remove GitHub Gist dependency (security improvement)
        print("Security notice: GitHub Gist key fetching has been disabled for security.")
        
    def get_active_key(self) -> Dict[str, Any]:
        """Get the current active key with rotation."""
        if not self._keys:
            return __ERROR_KEY__
            
        # Filter valid keys
        valid_keys = [k for k in self._keys if k.get('valid') == 'True']
        if not valid_keys:
            print("Warning: No valid API keys available.")
            return __ERROR_KEY__
            
        # Rotate through valid keys
        key = self.key_manager.rotate_keys(valid_keys)
        return key
        
    def get_keys_for_legacy_compatibility(self) -> List[Dict[str, Any]]:
        """Get keys in legacy format for backward compatibility."""
        return self._keys or []


# Global instance for backward compatibility
_api_key_provider = APIKeyProvider()


# Legacy API compatibility functions
def getNum() -> int:
    """Get number of available keys."""
    keys = _api_key_provider.get_keys_for_legacy_compatibility()
    return len(keys)


def getItem(index: int) -> Dict[str, Any]:
    """Get key by index."""
    keys = _api_key_provider.get_keys_for_legacy_compatibility()
    if index < 0 or index >= len(keys):
        return __ERROR_KEY__
    return keys[index]


def isItemValid(index: int) -> bool:
    """Check if key at index is valid."""
    item = getItem(index)
    return item.get("valid") == "True"


def getItems() -> List[Dict[str, Any]]:
    """Get all keys."""
    return _api_key_provider.get_keys_for_legacy_compatibility()


def getLimitIndexs() -> List[str]:
    """Get list of valid indices."""
    keys = _api_key_provider.get_keys_for_legacy_compatibility()
    return [str(i) for i in range(len(keys))]


def getVersion() -> str:
    """Get API version."""
    return "1.0.1-secure"


# New secure API functions
def get_secure_key() -> Dict[str, Any]:
    """Get a secure, rotated API key."""
    return _api_key_provider.get_active_key()


def get_secure_headers() -> Dict[str, str]:
    """Get randomized headers for API requests."""
    return _api_key_provider.header_manager.get_api_headers()


def setup_secure_session() -> requests.Session:
    """Create a secure session with randomized headers."""
    return _api_key_provider.header_manager.get_session_with_headers()
