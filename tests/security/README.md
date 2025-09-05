# Security Test Suite for tidal-dl-ng

This test suite provides comprehensive security testing for the tidal-dl-ng project, covering vulnerabilities, security features, and integration status.

## Test Structure

### 1. **test_api_keys.py**
Tests for API key security including:
- Hardcoded key detection
- Environment variable priority
- Key rotation functionality
- Secure storage encryption/decryption
- Header integration

### 2. **test_decryption.py**
Tests for decryption security including:
- Hardcoded master key detection
- Secure mode vs legacy mode
- Environment variable support
- Machine-specific key derivation

### 3. **test_headers.py**
Tests for request header security including:
- User-Agent diversity and randomization
- Header variety and optional fields
- Session management with headers
- Browser simulation capabilities

### 4. **test_request_patterns.py**
Tests for request pattern obfuscation including:
- Dynamic delay generation
- Time-of-day and session-based factors
- Burst mode behavior
- Download order randomization
- Session pause logic

### 5. **test_metadata.py**
Tests for metadata obfuscation including:
- Field order randomization
- Text variations and capitalization
- Optional field handling
- Replay gain obfuscation

### 6. **test_security_config.py**
Tests for security configuration and integration including:
- Proxy configuration
- Download delay settings
- Environment variable handling
- **Vulnerability tracking tests**

## Running the Tests

### Run all security tests:
```bash
python -m pytest tests/security/ -v
```

### Run specific test categories:
```bash
# Run only vulnerability tracking tests
python -m pytest tests/security/test_security_config.py::TestSecurityVulnerabilityTracking -v

# Run API key tests
python -m pytest tests/security/test_api_keys.py -v

# Run with markers
python -m pytest -m "security" -v
python -m pytest -m "vulnerability" -v
```

### Run with coverage:
```bash
python -m pytest tests/security/ --cov=tidal_dl_ng --cov-report=html
```

## Vulnerability Tracking

The test suite includes special vulnerability tracking tests that:
- **Document current vulnerabilities** 
- **Will fail when vulnerabilities are fixed**
- **Track security improvement progress**

Current tracked vulnerabilities:
1. Hardcoded API keys in source code
2. Hardcoded decryption master key
3. Metadata obfuscation not integrated
4. Secure mode not default
5. Proxy support not integrated

## Expected Test Results

### ✅ All tests should pass initially
This indicates that:
- Security modules are working correctly
- Vulnerabilities are properly documented
- Integration points are identified

### ❌ Vulnerability tests will fail when fixed
When a vulnerability is fixed, the corresponding test will fail with a message like:
```
"FIXED: Hardcoded keys removed!"
```

This is the desired outcome and indicates security improvements.

## Security Improvements Checklist

Based on the test suite findings:

- [ ] Remove hardcoded API keys from `api.py`
- [ ] Remove hardcoded decryption key from `decryption.py`
- [ ] Make secure mode the default
- [ ] Integrate metadata obfuscation in `download.py`
- [ ] Implement proxy support in download logic
- [ ] Enable security features by default
- [ ] Add download order randomization
- [ ] Apply headers to all HTTP requests

## Adding New Security Tests

When adding new security tests:
1. Place them in the appropriate test file
2. Use descriptive test names
3. Add appropriate markers (`@pytest.mark.security`)
4. Document expected behavior
5. Include vulnerability tracking if applicable

## Integration with CI/CD

These tests should be run:
- On every pull request
- Before releases
- As part of security audits
- Periodically to track vulnerability fixes

## Notes

- Tests use mocking where appropriate to avoid external dependencies
- Environment variables are reset between tests via `conftest.py`
- Some tests document current insecure behavior (vulnerability tracking)
- Tests are designed to help track security improvement progress
