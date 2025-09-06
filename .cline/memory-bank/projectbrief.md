# Project Brief: TIDAL Downloader Next Generation

## Overview
TIDAL Downloader Next Generation (tidal-dl-ng) is a Python-based application that enables users to download high-quality audio and video content from the TIDAL streaming service. The project provides both command-line interface (CLI) and graphical user interface (GUI) versions to accommodate different user preferences.

## Core Requirements
- **Primary Function**: Download songs, videos, albums, playlists, and favorites from TIDAL
- **Quality Support**: Audio quality up to HiRes Lossless/TIDAL MAX (24-bit, 192 kHz)
- **Performance**: Multithreaded and multi-chunked downloads for optimal speed
- **User Interfaces**: Both CLI (`tidal-dl-ng`) and GUI (`tidal-dl-ng-gui`) versions
- **Platform Support**: Cross-platform (Windows, macOS, Linux)
- **Python Version**: Requires Python 3.12

## Key Features
- Download tracks, videos, albums, playlists, user favorites
- Metadata extraction and embedding for downloaded content
- Adjustable audio and video download quality
- FLAC extraction from MP4 containers
- Lyrics and album art/cover download
- Playlist file creation
- Symbolic linking option to avoid duplicate files across playlists

## Target Users
- Music enthusiasts with paid TIDAL subscriptions
- Users seeking high-quality audio downloads
- Both technical users (CLI) and non-technical users (GUI)

## Technical Constraints
- Requires a paid TIDAL plan for access
- Educational purposes only (with disclaimer about distribution/piracy)
- Must comply with TIDAL's terms of service
- Python 3.12 requirement for compatibility

## Project Status
- Current version: 0.25.6
- Development status: Beta
- Active development with regular releases
- Community contributions welcome

## Success Criteria
- Reliable downloads across all supported content types
- Intuitive user experience in both CLI and GUI modes
- Maintains high audio quality standards
- Stable performance across platforms
- Active community engagement and support
