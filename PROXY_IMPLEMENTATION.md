# Proxy Implementation in tidal-dl-ng

## Overview

A comprehensive proxy system has been implemented to route all network traffic through configured proxy servers. This addresses the security vulnerability where network requests were previously made directly without proxy support.

## Implementation Details

### 1. ProxyManager Class (`tidal_dl_ng/security/proxy_manager.py`)

A centralized proxy management class that:
- Reads proxy configuration from application settings
- Supports HTTP, HTTPS, and SOCKS5 proxy types
- Handles proxy authentication with proper URL encoding
- Provides proxy configuration dictionaries for requests
- Includes proxy connection testing functionality
- **Smart proxy selection based on request protocol**

### 2. Proxy Settings Configuration

The following proxy settings are available in `tidal_dl_ng/model/cfg.py`:
- `proxy_enabled`: Enable/disable proxy usage
- `proxy_type`: Type of proxy (HTTP, HTTPS, SOCKS5, HTTP|HTTPS, or empty)
- `proxy_host`: Proxy server hostname or IP
- `proxy_port`: Proxy server port
- `proxy_use_auth`: Enable proxy authentication
- `proxy_username`: Username for proxy authentication
- `proxy_password`: Password for proxy authentication

### 3. Updated Components

#### Download Module (`tidal_dl_ng/download.py`)
- Download class now initializes ProxyManager
- All network requests use proxy settings:
  - Segment downloads
  - HEAD requests for file size
  - Cover image downloads
  - Video m3u8 playlist downloads via RequestsClient

#### RequestsClient (`tidal_dl_ng/download.py`)
- Updated to accept ProxyManager instance
- Applies proxy settings to all requests

#### Version Check (`tidal_dl_ng/__init__.py`)
- Latest version check now uses proxy settings

### 4. Test Suite (`tests/security/test_proxy.py`)

Comprehensive tests covering:
- Proxy configuration scenarios
- Authentication handling
- URL encoding of special characters
- Integration with download components
- Connection testing
- Empty proxy type handling
- HTTP|HTTPS proxy type support
- Case insensitive proxy type handling

## Usage

### GUI Configuration
Users can configure proxy settings through the settings dialog:
1. Open Settings dialog
2. Navigate to proxy settings section
3. Enable proxy and select type
4. Enter host, port, and authentication details if needed

### Programmatic Configuration
```python
settings = Settings()
settings.data.proxy_enabled = True
settings.data.proxy_type = "SOCKS5"  # or "HTTP", "HTTPS", "HTTP|HTTPS", or empty
settings.data.proxy_host = "proxy.example.com"
settings.data.proxy_port = 1080
settings.data.proxy_use_auth = True
settings.data.proxy_username = "user"
settings.data.proxy_password = "password"
settings.save()
```

## Security Benefits

1. **IP Address Masking**: All traffic goes through the proxy server
2. **Geographic Flexibility**: Can route traffic through different regions
3. **Network Policy Compliance**: Works with corporate proxy requirements
4. **Enhanced Privacy**: Reduces direct connection fingerprinting

## Supported Proxy Types

### HTTP Proxy
- Standard HTTP proxy for HTTP traffic only
- Configuration: `proxy_type = "HTTP"`
- Only HTTP requests will use this proxy

### HTTPS Proxy
- Secure proxy for HTTPS traffic only
- Configuration: `proxy_type = "HTTPS"`
- Only HTTPS requests will use this proxy

### SOCKS5 Proxy
- Full protocol support including DNS resolution
- Uses `socks5h://` to ensure DNS goes through proxy
- Configuration: `proxy_type = "SOCKS5"`
- Works for both HTTP and HTTPS requests

### Universal Proxy (HTTP|HTTPS)
- Use the same proxy for both HTTP and HTTPS traffic
- Configuration options:
  - `proxy_type = ""` (empty)
  - `proxy_type = "HTTP|HTTPS"`
  - `proxy_type = "HTTPS|HTTP"`
- This is the most common use case

## Smart Proxy Selection

The ProxyManager now intelligently selects the appropriate proxy based on the request protocol:

1. **Empty or "HTTP|HTTPS" proxy_type**: The proxy is used for both HTTP and HTTPS requests
2. **"HTTP" proxy_type**: Only HTTP requests use the proxy
3. **"HTTPS" proxy_type**: Only HTTPS requests use the proxy
4. **"SOCKS5" proxy_type**: Both HTTP and HTTPS requests use the SOCKS5 proxy

This ensures that:
- HTTP requests go through HTTP-capable proxies
- HTTPS requests go through HTTPS-capable proxies
- Users have full control over which protocols use the proxy

## Technical Notes

- Special characters in credentials are automatically URL-encoded
- Empty credentials are handled gracefully
- Proxy type is case-insensitive and trimmed of whitespace
- Invalid proxy types default to both HTTP and HTTPS for backward compatibility
- Proxy verification can be tested via `ProxyManager.test_proxy_connection()`
- All network requests inherit proxy settings automatically

## Implementation Checklist

✅ Created ProxyManager class  
✅ Added proxy settings to configuration  
✅ Updated Download class to use proxy  
✅ Updated RequestsClient for video downloads  
✅ Updated version check to use proxy  
✅ Added comprehensive test suite  
✅ Proxy settings available in GUI  
✅ Smart proxy selection based on request protocol  
✅ Support for empty proxy_type (defaults to both)  
✅ Support for "HTTP|HTTPS" proxy_type  

The proxy implementation is now complete and fully integrated into the application's network layer with smart protocol-based proxy selection.
