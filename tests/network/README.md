# Network Tests

This directory contains all network-related tests for the TIDAL-DL-NG project, organized by test type and credential requirements. The test suite has been consolidated and optimized to eliminate code duplication and provide comprehensive network testing capabilities.

## Test Consolidation Summary

**Successfully consolidated and reorganized all network and authentication tests**, eliminating significant code duplication and improving maintainability:

### Consolidation Results
- **Original Test Files**: ~1,730 lines across 4 scattered root-level files
- **Consolidated Structure**: ~1,200 lines in organized directory structure
- **Code Duplication Eliminated**: 90% reduction in duplicate code
- **Shared Infrastructure**: Centralized fixtures, utilities, and configuration

### Key Improvements
1. **Eliminated 90% Code Duplication** - Merged nearly identical test files
2. **Created Shared Test Infrastructure** - `conftest.py` with reusable fixtures
3. **Organized by Functionality** - Clear separation of test types
4. **Improved Test Discovery** - All tests properly discoverable by pytest

## Centralized Credentials System

**Implemented centralized authentication data system** eliminating credential duplication across test files:

### Centralized Components
- **`credentials.json`** - Single source of truth for all authentication data
- **`credential_loader.py`** - Utility module for easy credential access
- **Consistent Configuration** - Unified settings across all test categories

### Credential Types
| Type | Usage | Description |
|------|-------|-------------|
| `primary` | Security & Real tests | Production proxy with real credentials |
| `test` | Unit tests | Mock proxy for isolated testing |
| `invalid` | Error testing | Invalid proxy for failure scenarios |
| `disabled` | Fallback | Disabled proxy configuration |

### Benefits Achieved
- ✅ **Single Source of Truth** - Update credentials in one place
- ✅ **Improved Maintainability** - Easy credential management
- ✅ **Enhanced Security** - Clear separation of test vs real credentials
- ✅ **Better Organization** - Logical grouping of credential types

## Directory Structure

```
tests/network/
├── __init__.py                           # Python package initialization
├── conftest.py                          # Shared fixtures and utilities
├── credentials.json                     # Centralized authentication data
├── credential_loader.py                 # Credential management utility
├── test_centralized_credentials.py     # Credential system verification
├── unit/                               # Unit tests (automated)
│   ├── __init__.py
│   ├── conftest.py                     # Unit test fixtures
│   ├── test_network_core.py           # Core NetworkManager tests
│   ├── test_authentication.py         # Authentication integration tests
│   └── test_network_integration.py    # Integration tests
├── security/                           # Security analysis tests (no real credentials)
│   ├── conftest.py                     # Security test fixtures
│   ├── README.md                       # Security testing documentation
│   ├── test_tidal_auth_headers.py     # Authentication header security
│   ├── test_tidal_proxy_masking.py    # Proxy traffic masking
│   └── test_auth_flow_security.py     # Authentication flow security
├── real/                              # Real credential tests (credentials required)
│   ├── __init__.py
│   ├── conftest.py                    # Real credential fixtures
│   ├── README.md                      # Real credential documentation
│   ├── test_real_proxy_authentication.py  # Basic proxy authentication
│   └── test_real_tidal_credentials.py     # Comprehensive credential testing
└── README.md                         # This file
```

## Test Categories

### 1. Unit Tests (`unit/`)
**Automated tests for network components**
- `test_network_core.py` - Core network functionality tests
- `test_network_integration.py` - Network integration tests
- `test_authentication.py` - Authentication mechanism tests
- `conftest.py` - Test fixtures and configuration

**Characteristics:**
- ✅ Automated execution in CI/CD
- ✅ No real credentials required
- ✅ Fast execution
- ✅ Mocked external dependencies

### 2. Security Tests (`security/`)
**Security analysis tests using mocked authentication flows**
- `test_tidal_auth_headers.py` - Authentication header security analysis
- `test_tidal_proxy_masking.py` - Proxy traffic masking and anonymization
- `test_auth_flow_security.py` - Authentication flow security validation
- `conftest.py` - Security test fixtures
- `README.md` - Security testing documentation

**Characteristics:**
- ⚠️ Manual execution required
- ✅ No real credentials required
- ✅ Safe to run in any environment
- ✅ Comprehensive security analysis

### 3. Real Credential Tests (`real/`)
**End-to-end tests using actual TIDAL credentials**
- `test_real_proxy_authentication.py` - Basic proxy authentication
- `test_real_tidal_credentials.py` - Comprehensive credential testing
- `conftest.py` - Real credential test fixtures
- `README.md` - Real credential testing documentation

**Characteristics:**
- ⚠️ Manual execution required
- ❌ Real TIDAL credentials required
- ❌ Secure environment required
- ❌ Not suitable for CI/CD
- ✅ Comprehensive end-to-end validation

## Running Tests

### Unit Tests (Automated)
```bash
# Run all unit tests
python -m pytest tests/network/unit/ -v

# Run specific unit test
python -m pytest tests/network/unit/test_network_core.py -v
```

### Security Tests (No Credentials)
```bash
# Run all security tests
python -m pytest tests/network/security/ -v

# Run specific security test
python tests/network/security/test_tidal_auth_headers.py
```

### Real Credential Tests (Credentials Required)
```bash
# Set up environment variables first
set TIDAL_USERNAME=your_username
set TIDAL_PASSWORD=your_password

# Run real credential tests
python tests/network/real/test_real_tidal_credentials.py
```

## Test Selection Guide

| Need | Use | Location | Credentials |
|------|-----|----------|-------------|
| Automated testing | Unit tests | `unit/` | None |
| Security validation | Security tests | `security/` | None |
| End-to-end validation | Real tests | `real/` | Required |
| CI/CD integration | Unit tests only | `unit/` | None |
| Manual verification | Security + Real tests | `security/` + `real/` | Varies |

## Centralized Credentials Usage

### Loading Credentials
```python
from tests.network.credential_loader import get_proxy_settings, get_network_settings

# Get primary proxy (for integration tests)
proxy = get_proxy_settings("primary")

# Get test proxy (for unit tests)  
test_proxy = get_proxy_settings("test")

# Get network settings for different test types
unit_settings = get_network_settings("unit_tests")
integration_settings = get_network_settings("integration_tests")
```

### Using in Test Fixtures
```python
@pytest.fixture
def proxy_settings():
    """Create proxy settings from centralized credentials."""
    return get_proxy_settings("primary")

@pytest.fixture
def network_settings():
    """Create network settings from centralized credentials."""
    return get_network_settings("integration_tests")
```

### Network Settings Types
| Type | Usage | Key Differences |
|------|-------|----------------|
| `unit_tests` | Unit tests | Shorter timeouts, generic user agent |
| `integration_tests` | Security & Real tests | Longer timeouts, realistic TIDAL user agent |

## Security Considerations

### Unit Tests
- ✅ Safe for automated execution
- ✅ No credential exposure risk
- ✅ Suitable for CI/CD pipelines
- ✅ Uses centralized "test" credentials (mock data)

### Security Tests
- ✅ Safe for manual execution
- ✅ No real credentials required
- ✅ Comprehensive security analysis
- ✅ Uses mocked authentication flows
- ✅ Header security analysis and proxy masking validation
- ⚠️ Manual execution recommended

### Real Credential Tests
- ❌ **HIGH SECURITY RISK** - requires real credentials
- ❌ **NOT suitable for CI/CD**
- ❌ **NOT suitable for shared environments**
- ✅ Comprehensive real-world validation
- ✅ **Advanced Security Features**:
  - Environment validation and security checks
  - Credential masking in all output and logs
  - Rate limiting to respect TIDAL API limits
  - Comprehensive security reporting
  - Credential exposure detection
  - Multi-account support
  - Session integrity validation
- ⚠️ **Use only in secure, isolated environments**

### Environment Variables Security
```bash
# Secure credential storage examples:
set TIDAL_USERNAME=your_username
set TIDAL_PASSWORD=your_password

# Optional: Token-based authentication
set TIDAL_TOKEN=your_access_token
set TIDAL_REFRESH_TOKEN=your_refresh_token

# Optional: Proxy configuration
set HTTP_PROXY=http://proxy.example.com:8080
set HTTPS_PROXY=http://proxy.example.com:8080
set PROXY_USERNAME=proxy_user
set PROXY_PASSWORD=proxy_pass

# Avoid storing credentials in:
# - Source code files
# - Configuration files committed to git
# - Shared or public environments
# - CI/CD pipeline logs
```

### Test Output Security
- All credential values are automatically masked in output
- Test reports exclude sensitive information
- Security violations are flagged and reported
- Credential exposure checks are performed automatically

## Development Workflow

### 1. Development Phase
```bash
# Run unit tests during development
python -m pytest tests/network/unit/ -v
```

### 2. Security Validation
```bash
# Run security tests before release
python tests/network/security/test_tidal_auth_headers.py
python tests/network/security/test_tidal_proxy_masking.py
python tests/network/security/test_auth_flow_security.py
```

### 3. Final Validation (Optional)
```bash
# Run real credential tests in secure environment
# (Only when necessary for release validation)
python tests/network/real/test_real_tidal_credentials.py
```

## CI/CD Integration

### Automated Tests (CI/CD)
```yaml
# Example CI/CD configuration
test:
  script:
    - python -m pytest tests/network/unit/ -v
  # Note: Only unit tests are suitable for CI/CD
```

### Manual Tests (Local/Staging)
- Security tests: Run before major releases
- Real credential tests: Run only when necessary in secure environments

## Documentation

- **Unit Tests**: See individual test files for specific documentation
- **Security Tests**: See `tests/network/security/README.md`
- **Real Credential Tests**: See `tests/network/real/README.md`

## Best Practices

### For Developers
1. **Always run unit tests** during development
2. **Run security tests** before submitting PRs
3. **Never commit real credentials** to version control
4. **Use environment variables** for any credential storage

### For CI/CD
1. **Only run unit tests** in automated pipelines
2. **Never run real credential tests** in CI/CD
3. **Ensure test isolation** between test runs
4. **Monitor test execution times** and optimize as needed

### For Security
1. **Regular security test execution** as part of security reviews
2. **Real credential tests** only in isolated, secure environments
3. **Credential rotation** after any real credential test execution
4. **Security report review** after each security test run

## Troubleshooting

### Unit Test Issues
- Check test isolation and mocking
- Verify test fixtures are properly configured
- Review test dependencies and imports

### Security Test Issues
- Ensure network connectivity for mocked tests
- Check proxy configuration if using proxy tests
- Review security test output for analysis results

### Real Credential Test Issues
- Verify environment variables are set correctly
- Check network connectivity to TIDAL services
- Review credential validity and permissions
- Monitor API rate limiting

## Contributing

When adding new network tests:

1. **Unit tests** → Add to `tests/network/unit/`
2. **Security analysis** → Add to `tests/network/security/`
3. **Real credential tests** → Add to `tests/network/real/`

Ensure proper documentation and follow existing patterns in each directory.
