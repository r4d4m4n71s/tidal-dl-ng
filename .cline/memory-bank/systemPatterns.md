# System Patterns: TIDAL Downloader Next Generation

## Architecture Overview

TIDAL-dl-ng follows a modular Python architecture with clear separation of concerns between CLI, GUI, core business logic, and supporting utilities.

```
tidal_dl_ng/
├── cli.py              # Command-line interface entry point
├── gui.py              # GUI application entry point
├── api.py              # TIDAL API interaction layer
├── config.py           # Configuration management
├── download.py         # Core download logic
├── metadata.py         # Metadata extraction/processing
├── worker.py           # Background task management
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
- **Location**: `config.py`
- **Pattern Benefits**: Single source of truth for application settings

### 5. API Wrapper Pattern
- **Implementation**: Abstraction layer over TIDAL API
- **Purpose**: Handles authentication, API calls, error handling
- **Location**: `api.py`
- **Dependencies**: Uses `tidalapi` library as foundation

## Component Relationships

### Core Flow Architecture
```
User Input (CLI/GUI) → Configuration → API Layer → Download Engine → Worker Threads → File Output
                                                        ↓
                                                   Metadata Processing
```

### Dependency Hierarchy
1. **Entry Points** (`cli.py`, `gui.py`) depend on:
2. **Core Logic** (`download.py`, `api.py`) depends on:
3. **Data Models** (`model/`) and **Helpers** (`helper/`)
4. **External Libraries** (tidalapi, requests, mutagen, etc.)

## Critical Implementation Paths

### Download Workflow
1. **Authentication**: User credentials → TIDAL API authentication
2. **Content Resolution**: URL/ID → TIDAL content metadata
3. **Quality Selection**: User preferences → optimal available quality
4. **Download Execution**: Multithreaded/chunked download
5. **Metadata Processing**: Extract/embed metadata, lyrics, artwork
6. **File Organization**: Apply naming patterns, create playlists

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

### Configuration Flow
- **Sources**: Default values → Config files → CLI arguments → Runtime changes
- **Persistence**: TOML format for human-readable configuration
- **Access Pattern**: Global configuration object accessible throughout application

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
- **TIDAL API**: Primary content source via tidalapi library
- **FFmpeg**: Media processing (when `extract_flac` enabled)
- **File System**: Cross-platform path handling via pathvalidate

### Library Integration Strategy
- **Core Dependencies**: Minimal, well-established libraries
- **Optional Dependencies**: GUI components as optional extras
- **Version Pinning**: Specific versions to ensure stability

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

### Credential Management
- **No Plain Text Storage**: Credentials handled through TIDAL's authentication
- **Session Management**: Proper session handling and expiration
- **API Key Protection**: Secure handling of TIDAL API interactions

### File System Security
- **Path Validation**: Prevent directory traversal attacks
- **Permission Checking**: Verify write permissions before downloads
- **Sanitization**: Clean filenames to prevent security issues
