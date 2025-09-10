# Network Flow Diagrams - Visual Reference

This directory contains visual representations of the TIDAL-DL-NG network flow diagrams.

## Diagram Files

### 01. Table of Contents
- **File**: `01_table_of_contents.png`
- **Source**: `01_table_of_contents.mmd`

### 02. Authentication Flow Overview
- **File**: `02_authentication_flow_overview.png`
- **Source**: `02_authentication_flow_overview.mmd`

### 03. Token-Based Authentication Flow
- **File**: `03_token_based_authentication_flow.png`
- **Source**: `03_token_based_authentication_flow.mmd`

### 04. OAuth Device Linking Flow
- **File**: `04_oauth_device_linking_flow.png`
- **Source**: `04_oauth_device_linking_flow.mmd`

### 05. Authentication Method Decision Tree
- **File**: `05_authentication_method_decision_tree.png`
- **Source**: `05_authentication_method_decision_tree.mmd`

### 06. Download Flow Process
- **File**: `06_download_flow_process.png`
- **Source**: `06_download_flow_process.mmd`

### 07. Error Handling & Proxy Troubleshooting
- **File**: `07_error_handling_proxy_troubleshooting.png`
- **Source**: `07_error_handling_proxy_troubleshooting.mmd`

### 08. Session Management & Caching
- **File**: `08_session_management_caching.png`
- **Source**: `08_session_management_caching.mmd`


## Usage

These diagrams provide visual documentation of:
- System architecture and component relationships
- Authentication flows (token-based vs OAuth)
- Download processes and session management
- Error handling and proxy troubleshooting
- Session caching and management

## Formats Available

- **PNG Images**: High-quality raster images suitable for embedding in documentation
- **Mermaid Source**: `.mmd` files that can be edited and re-rendered
- **Configuration**: `mermaid-config.json` for consistent styling

## Regenerating Diagrams

To regenerate the diagrams from source:

```bash
python extract_diagrams.py
```

Or manually using Mermaid CLI:

```bash
mmdc -i diagram.mmd -o diagram.png -c mermaid-config.json -w 1200 -H 800 --backgroundColor white
```
