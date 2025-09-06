# Technical Context: TIDAL Downloader Next Generation

## Core Technologies

### Programming Language
- **Python 3.12**: Strict requirement (>=3.12,<3.13)
- **Reason**: Leverages latest Python features and type system improvements
- **Compatibility**: Single version to reduce testing matrix complexity

### Package Management
- **Poetry**: Primary dependency and build management
- **pyproject.toml**: Modern Python project configuration
- **Benefits**: Deterministic builds, dependency resolution, virtual environment management

### Framework Stack
- **CLI Framework**: Typer for command-line interface
- **GUI Framework**: PySide6 (Qt6) for cross-platform GUI
- **HTTP Client**: Requests library for API communication
- **Audio Processing**: Mutagen for metadata manipulation

## Key Dependencies

### Core Dependencies
```toml
requests = "~2.32.3"              # HTTP client for API calls
mutagen = "^1.47.0"               # Audio metadata processing
dataclasses-json = "^0.6.7"       # JSON serialization
pathvalidate = "^3.2.3"           # Cross-platform path validation
m3u8 = "^6.0.0"                   # M3U8 playlist processing
coloredlogs = "^15.0.1"           # Enhanced logging output
mpegdash = "^0.4.0"               # MPEG-DASH streaming support
rich = "^13.9.4"                  # Rich terminal output
toml = "^0.10.2"                  # Configuration file parsing
typer = "^0.15.2"                 # CLI framework
tidalapi = "^0.8.3"               # TIDAL API wrapper
python-ffmpeg = "^2.0.12"         # FFmpeg integration
pycryptodome = "^3.22.0"          # Cryptographic functions
```

### Optional GUI Dependencies
```toml
pyside6 = "6.8.0.1"                    # Qt6 GUI framework
pyqtdarktheme-fork = "^2.3.2"          # Dark theme support
```

### Development Dependencies
- **Testing**: pytest, pytest-cov for test coverage
- **Code Quality**: black, isort, ruff, mypy for code formatting/linting
- **Security**: bandit for security analysis
- **Documentation**: mkdocs with material theme
- **Build**: nuitka for binary compilation

## Development Environment Setup

### Installation Process
```bash
# Install Poetry (package manager)
pipx install --upgrade poetry

# Install all dependencies including dev and docs
poetry install --all-extras --with dev,docs

# Activate virtual environment
poetry shell
```

### Entry Points
- **CLI**: `tidal-dl-ng` → `tidal_dl_ng.cli:app`
- **GUI**: `tidal-dl-ng-gui` → `tidal_dl_ng.gui:gui_activate`
- **CLI Short**: `tdn` → `tidal_dl_ng.cli:app`  
- **GUI Short**: `tdng` → `tidal_dl_ng.gui:gui_activate`

## Build System

### Modern Python Build
- **Build Backend**: Poetry Core masonry API
- **Configuration**: All build config in pyproject.toml
- **Standards Compliance**: PEP 517/518 compatible

### GUI Development Workflow
```bash
# Launch Qt Designer with plugins
PYSIDE_DESIGNER_PLUGINS=tidal_dl_ng/ui pyside6-designer

# Convert UI files to Python
pyside6-uic tidal_dl_ng/ui/main.ui -o tidal_dl_ng/ui/main.py
```

### Binary Build Process
```bash
# Build process via Makefile
make install      # Setup environment
make gui-macos    # Build macOS GUI binary
# Additional platform-specific builds available
```

## Technical Constraints

### Python Version Lock
- **Strict Requirement**: Python 3.12 only
- **Rationale**: Latest features, security patches, performance improvements
- **Impact**: Limits deployment to systems with Python 3.12

### Platform Considerations
- **Cross-platform Support**: Windows, macOS, Linux
- **GUI Framework**: Qt6 for native look/feel on each platform
- **Path Handling**: pathvalidate ensures cross-platform compatibility
- **Binary Distribution**: Platform-specific builds required

### API Dependencies
- **TIDAL API**: Requires active TIDAL subscription
- **API Stability**: Dependent on TIDAL's API changes
- **Rate Limiting**: Must respect TIDAL's API rate limits
- **Authentication**: OAuth-based authentication flow

## Code Quality Standards

### Linting and Formatting
- **Code Formatter**: Black with 120 character line length
- **Import Sorting**: isort with black profile
- **Linting**: Ruff with comprehensive rule set
- **Type Checking**: mypy with strict settings

### Code Quality Rules
```python
# Ruff configuration highlights
line-length = 120
target-version = "py312"
# Extensive rule selection covering security, style, complexity
```

### Testing Strategy
- **Framework**: pytest with coverage reporting
- **Structure**: Tests in dedicated `tests/` directory
- **Coverage**: pytest-cov for coverage analysis
- **Security**: bandit for security vulnerability scanning

## Performance Considerations

### Download Performance
- **Multithreading**: Concurrent downloads for playlists/albums
- **Chunked Downloads**: Large files split for reliability
- **Connection Reuse**: HTTP connection pooling
- **Memory Efficiency**: Streaming processing for large files

### GUI Performance
- **Background Processing**: Worker threads prevent UI blocking
- **Progress Updates**: Efficient progress reporting
- **Resource Management**: Proper cleanup of Qt resources

## Integration Tools

### External Tool Integration
- **FFmpeg**: Optional FLAC extraction from MP4 containers
- **Qt Designer**: Visual GUI design and modification
- **Git Hooks**: pre-commit hooks for code quality enforcement

### Development Tools
- **Make**: Build automation via Makefile
- **Tox**: Testing across multiple environments
- **MkDocs**: Documentation generation and hosting
- **GitHub Actions**: CI/CD pipeline automation

## Deployment Patterns

### Installation Methods
1. **PyPI Package**: `pip install tidal-dl-ng[gui]`
2. **Binary Releases**: Platform-specific executables
3. **Source**: Direct from Git repository with Poetry

### Distribution Strategy
- **Core Package**: CLI-only for minimal installs
- **GUI Extra**: Optional GUI components
- **Platform Binaries**: Standalone executables for each platform
- **Package Managers**: Available through pip/PyPI

## Security Architecture

### Credential Handling
- **No Storage**: Credentials not stored locally
- **Session Management**: Secure token handling via tidalapi
- **Encryption**: pycryptodome for cryptographic needs

### File System Security
- **Path Validation**: Prevents directory traversal
- **Permission Checks**: Validates write access before downloads
- **Sanitization**: Secure filename handling across platforms
