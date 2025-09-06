# Active Context: TIDAL Downloader Next Generation

## Current Work Focus

### Memory Bank Initialization (Current Session)
- **Status**: Initializing complete project memory bank for first time
- **Goal**: Create comprehensive documentation foundation for future development sessions
- **Progress**: Core memory bank files created, establishing project knowledge base

### Project Current State
- **Version**: 0.25.6 (Beta)
- **Development Status**: Active open-source project with regular commits
- **Repository**: https://github.com/r4d4m4n71s/tidal-dl-ng.git (fork of original exislow/tidal-dl-ng)
- **Latest Commit**: d9ab28d8840c8616d11f5610a78a02b90fb7e696

## Recent Changes & Evolution

### Project Structure Analysis
- **Modern Python Setup**: Using Poetry for dependency management
- **Dual Interface**: Both CLI (Typer) and GUI (PySide6) implementations
- **Code Quality**: Comprehensive linting setup (ruff, black, mypy)
- **Documentation**: MkDocs with material theme for project docs

### Key Discovery Points
- **Entry Points**: Multiple CLI shortcuts (`tidal-dl-ng`, `tdn`) and GUI launchers
- **Architecture**: Clean separation between CLI, GUI, core logic, and helpers
- **Dependencies**: Well-maintained dependency list with optional GUI components
- **Build System**: Cross-platform support with platform-specific binary builds

## Next Steps & Priorities

### Immediate Development Focus
1. **Code Review**: Examine core modules (api.py, download.py, worker.py) for functionality
2. **Testing Assessment**: Review test coverage and identify testing gaps
3. **Feature Analysis**: Understand current feature set vs roadmap items
4. **Issue Tracking**: Review open issues and community feedback

### Memory Bank Maintenance
- **Regular Updates**: Keep activeContext.md current with ongoing work
- **Pattern Documentation**: Record new architectural decisions and patterns
- **Progress Tracking**: Maintain accurate status of development milestones

## Active Decisions & Considerations

### Development Environment
- **Python Version**: Strict 3.12 requirement maintained for latest features
- **Dependencies**: Balancing feature richness vs minimal dependency footprint
- **Optional Components**: GUI components as optional extras for flexible installation

### Architecture Decisions
- **Framework Choices**: Typer for CLI, PySide6 for GUI proven effective
- **Code Organization**: Modular structure supports both interface types
- **Performance Strategy**: Multithreaded downloads with chunked processing

## Important Patterns & Preferences

### Code Style Standards
- **Line Length**: 120 characters (configured in black, ruff)
- **Import Organization**: isort with black profile for consistency
- **Type Annotations**: mypy strict mode enforced throughout codebase
- **Error Handling**: Comprehensive exception handling with user-friendly messages

### Development Workflow
- **GUI Development**: Qt Designer → .ui files → pyside6-uic → Python modules
- **Build Process**: Poetry for dependency management, Makefile for build automation
- **Quality Gates**: pre-commit hooks, comprehensive linting, security scanning

### User Experience Priorities
- **CLI Efficiency**: Single commands for common operations
- **GUI Usability**: Progressive disclosure, clear progress feedback
- **Cross-platform**: Consistent experience across Windows, macOS, Linux
- **Performance**: Optimized for large downloads with progress visibility

## Learning & Project Insights

### Technical Strengths
- **Modern Python**: Leverages latest Python 3.12 features effectively
- **Clean Architecture**: Well-separated concerns enable maintainability
- **Performance Focus**: Multithreading and chunking optimize download experience
- **Quality Standards**: Comprehensive tooling ensures code quality

### Project Maturity Indicators
- **Active Community**: Regular contributions and issue discussions
- **Documentation**: Comprehensive README with usage examples
- **CI/CD**: GitHub Actions for automated testing and releases
- **Distribution**: Multiple installation methods (pip, binaries, source)

### Development Environment Insights
- **Tooling Integration**: Poetry, pre-commit, and quality tools work seamlessly
- **Build System**: Modern Python packaging standards (PEP 517/518)
- **Cross-platform**: Thoughtful handling of platform differences

## Current Configuration State

### Project Settings
- **Version**: 0.25.6 (defined in pyproject.toml)
- **License**: GNU Affero General Public License v3
- **Python Support**: 3.12 only
- **Development Status**: Beta (4 - Beta in classifiers)

### Key File Locations
- **Main Modules**: tidal_dl_ng/{cli.py, gui.py, api.py, download.py}
- **Configuration**: pyproject.toml (Poetry), setup.cfg, .editorconfig
- **Documentation**: docs/ directory with MkDocs setup
- **Tests**: tests/ directory with pytest configuration

## Work Context Notes

### Development Flow Understanding
- **Entry Points**: Clear separation between CLI and GUI entry points
- **Core Logic**: Shared business logic used by both interfaces
- **External Dependencies**: Careful management of required vs optional deps
- **Quality Assurance**: Multiple layers of code quality enforcement

### Future Considerations
- **API Changes**: Monitor TIDAL API stability and authentication changes  
- **Performance**: Continue optimizing download performance and memory usage
- **Features**: Balance new feature requests with maintenance overhead
- **Community**: Maintain active engagement with user community and contributors
