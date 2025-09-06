# System Patterns: TIDAL Downloader Next Generation

## Architecture Overview

TIDAL-dl-ng follows a modular Python architecture with clear separation of concerns between CLI, GUI, core business logic, and supporting utilities. Recent refactoring has improved module organization and eliminated code duplication.

```
tidal_dl_ng/
├── cli.py              # Command-line interface entry point
├── gui.py              # GUI application entry point
├── api.py              # TIDAL API interaction layer
├── config.py           # Configuration management (cleaned up)
├── enhanced_session.py # Enhanced TIDAL session with proxy integration
├── proxy.py            # Proxy management and connectivity (consolidated)
├── download.py         # Core download logic
├── metadata.py         # Metadata extraction/processing
├── worker.py           # Background task management
├── auth_server.py      # OAuth authentication server
├── tidal_proxy_integration.py # Proxy integration utilities
├── helper/             # Utility modules
├── model/              # Data models and structures
├── ui/                 # GUI components and resources
└── security/           # Security-related functionality
```

## Key Design Patterns

### 1. Command Pattern (CLI Interface)
- **Implementation**: Uses Typer framework for command-line interface
- **Entry Points**: Multiple CLI commands (`dl`, `dl_fav`, `cfg`, `login`, `logout`, `gui`)
- **Pattern Benefits**: Clean command separation, easy extensibility
- **Location**: `cli.py` with Typer decorators

### 2. Model-View-Controller (GUI)
- **Model**: Data structures in `model/` directory
- **View**: Qt Designer `.ui` files and generated Python code in `ui/`
- **Controller**: GUI logic in `gui.py` and dialog modules
- **Pattern Benefits**: Separation of UI from business logic

### 3. Worker/Background Processing Pattern
- **Implementation**: Dedicated worker module for download tasks
- **Purpose**: Handles multithreaded downloads, progress tracking
- **Location**: `worker.py`
- **Integration**: Used by both CLI and GUI interfaces

### 4. Configuration Management Pattern
- **Implementation**: Centralized configuration handling
- **Features**: TOML-based configuration, runtime setting management
- **Location**: `config.py` (recently cleaned up, proxy methods moved to proxy.py)
- **Pattern Benefits**: Single source of truth for application settings

### 5. Enhanced Session Pattern (Recently Refactored)
- **Implementation**: EnhancedTidalSession class (renamed from ProxyEnhancedTidalSession)
- **Purpose**: Seamless integration of TIDAL API with proxy functionality
- **Location**: `enhanced_session.py`
- **Pattern Benefits**: Clean separation between session management and proxy operations

### 6. Proxy Management Pattern (Recently Consolidated)
- **Implementation**: ProxyManager class with comprehensive functionality
- **Features**: Proxy connectivity testing, status monitoring, location reporting
- **Location**: `proxy.py` (consolidated from multiple locations)
- **Pattern Benefits**: Single responsibility for all proxy-related operations

### 7. API Wrapper Pattern
- **Implementation**: Abstraction layer over TIDAL API
- **Purpose**: Handles authentication, API calls, error handling
- **Location**: `api.py`
- **Dependencies**: Uses `tidalapi` library as foundation

## Component Relationships

### Core Flow Architecture (Updated with Recent Changes)
```
User Input (CLI/GUI) → Configuration → Enhanced Session → API Layer → Download Engine → Worker Threads → File Output
                                            ↓                              ↓
                                       Proxy Manager                 Metadata Processing
```

### Dependency Hierarchy (Post-Refactoring)
1. **Entry Points** (`cli.py`, `gui.py`) depend on:
2. **Core Logic** (`download.py`, `api.py`, `enhanced_session.py`) depends on:
3. **Supporting Services** (`proxy.py`, `auth_server.py`, `config.py`) depends on:
4. **Data Models** (`model/`) and **Helpers** (`helper/`)
5. **External Libraries** (tidalapi, requests, mutagen, etc.)

### Recent Architectural Improvements
- **Proxy Method Consolidation**: All proxy operations now centralized in ProxyManager
- **Class Renaming**: EnhancedTidalSession provides clearer naming without proxy prefix
- **Method Delegation**: Enhanced session delegates proxy operations to dedicated manager
- **Code Deduplication**: Eliminated duplicate methods between config.py and proxy.py

## Critical Implementation Paths

### Download Workflow (Enhanced with Proxy Support)
1. **Authentication**: Multiple methods supported
   - Token-based authentication for existing sessions
   - LocalAuthServer for complete OAuth 2.0 flow
   - Device linking with proxy support
2. **Proxy Integration**: ProxyManager handles location masking and connectivity
3. **Content Resolution**: URL/ID → TIDAL content metadata (via EnhancedTidalSession)
4. **Quality Selection**: User preferences → optimal available quality
5. **Download Execution**: Multithreaded/chunked download with proxy support
6. **Metadata Processing**: Extract/embed metadata, lyrics, artwork
7. **File Organization**: Apply naming patterns, create playlists

### Authentication Flow (Recently Analyzed)
1. **Priority System**: Token → LocalAuthServer → Device Linking → Standard fallback
2. **Session Management**: EnhancedTidalSession maintains authentication state
3. **Proxy Integration**: Seamless proxy support across all authentication methods
4. **Error Handling**: Graceful fallback between authentication methods

### GUI Integration
1. **Qt Designer Workflow**: `.ui` files → `pyside6-uic` → Python modules
2. **Event Handling**: User interactions → business logic calls
3. **Progress Feedback**: Worker signals → GUI updates
4. **Dialog Management**: Settings, login, version dialogs

### CLI Command Processing
1. **Typer Framework**: Command parsing and validation
2. **Configuration Loading**: Read settings from config files
3. **Business Logic Delegation**: Route to appropriate core functions
4. **Output Formatting**: Rich library for enhanced terminal output

## Data Flow Patterns

### Configuration Flow (Recently Improved)
- **Sources**: Default values → Config files → CLI arguments → Runtime changes
- **Persistence**: TOML format for human-readable configuration
- **Access Pattern**: Global configuration object accessible throughout application
- **Proxy Configuration**: Centralized in ProxyManager, accessed via delegation
- **Authentication Settings**: Multiple authentication method configurations supported

### Enhanced Session Data Flow (New Pattern)
```
Authentication Request → EnhancedTidalSession → ProxyManager → TIDAL API → Response Processing
                                ↓
                         Session State Management
```

### Download Data Flow
```
TIDAL URL → API Resolution → Media URLs → Chunked Downloads → File Assembly → Metadata Embedding
```

### Error Handling Pattern
- **API Errors**: Wrapper exceptions with user-friendly messages  
- **Network Errors**: Retry logic with exponential backoff
- **File System Errors**: Graceful handling with alternative paths
- **User Errors**: Validation with clear error messages

## Integration Points

### External Service Integration
- **TIDAL API**: Primary content source via tidalapi library with enhanced session management
- **Proxy Services**: Integration with proxy providers for location masking
- **OAuth Providers**: Local HTTP server for OAuth callback handling
- **FFmpeg**: Media processing (when `extract_flac` enabled)
- **File System**: Cross-platform path handling via pathvalidate

### Library Integration Strategy
- **Core Dependencies**: Minimal, well-established libraries
- **Optional Dependencies**: GUI components as optional extras
- **Version Pinning**: Specific versions to ensure stability
- **Proxy Libraries**: Integrated proxy support without additional dependencies
- **Authentication Libraries**: OAuth 2.0 support with local server capabilities

## Performance Patterns

### Download Optimization
- **Multithreading**: Parallel downloads for playlists/albums
- **Chunked Downloads**: Large files split into chunks for reliability
- **Connection Pooling**: Reuse HTTP connections for efficiency

### Memory Management
- **Streaming Processing**: Large files processed in chunks
- **Resource Cleanup**: Proper cleanup of network connections and file handles
- **Progress Tracking**: Efficient progress reporting without performance impact

## Security Considerations

### Credential Management (Enhanced)
- **No Plain Text Storage**: Credentials handled through TIDAL's authentication
- **Multiple Auth Methods**: Secure handling of different authentication flows
- **Session Management**: Proper session handling and expiration via EnhancedTidalSession
- **API Key Protection**: Secure handling of TIDAL API interactions
- **OAuth Security**: Local server with proper callback handling and state validation

### Network Security
- **Proxy Security**: Secure proxy configuration and connection handling
- **TLS/SSL**: Encrypted connections for all API communications
- **Request Validation**: Proper validation of API responses and proxy status

### File System Security
- **Path Validation**: Prevent directory traversal attacks
- **Permission Checking**: Verify write permissions before downloads
- **Sanitization**: Clean filenames to prevent security issues
