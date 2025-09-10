#!/usr/bin/env python3
"""
Extract Mermaid diagrams from NETWORK_FLOW_DIAGRAMS.md and convert them to visual formats.
"""

import re
import os
import subprocess
import sys
from pathlib import Path

def extract_mermaid_diagrams(markdown_file):
    """Extract all Mermaid diagrams from the markdown file."""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all mermaid code blocks
    pattern = r'```mermaid\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # Extract diagram titles from headers
    title_pattern = r'## (.+?)\n\n.*?```mermaid'
    titles = re.findall(title_pattern, content, re.DOTALL)
    
    diagrams = []
    for i, (title, diagram) in enumerate(zip(titles, matches)):
        # Clean up title for filename
        filename = re.sub(r'[^\w\s-]', '', title.lower())
        filename = re.sub(r'[-\s]+', '_', filename)
        filename = f"{i+1:02d}_{filename}"
        
        diagrams.append({
            'title': title,
            'filename': filename,
            'content': diagram.strip()
        })
    
    return diagrams

def create_mermaid_files(diagrams, output_dir):
    """Create individual .mmd files for each diagram."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    created_files = []
    for diagram in diagrams:
        mmd_file = output_dir / f"{diagram['filename']}.mmd"
        
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(diagram['content'])
        
        created_files.append(mmd_file)
        print(f"Created: {mmd_file}")
    
    return created_files

def create_mermaid_config():
    """Create a Mermaid configuration file for better styling."""
    config = {
        "theme": "default",
        "themeVariables": {
            "primaryColor": "#e1f5fe",
            "primaryTextColor": "#000000",
            "primaryBorderColor": "#0277bd",
            "lineColor": "#0277bd",
            "secondaryColor": "#f3e5f5",
            "tertiaryColor": "#e8f5e8",
            "background": "#ffffff",
            "mainBkg": "#ffffff",
            "secondBkg": "#f5f5f5",
            "tertiaryBkg": "#fafafa"
        },
        "flowchart": {
            "nodeSpacing": 50,
            "rankSpacing": 50,
            "curve": "basis"
        }
    }
    
    import json
    with open('diagrams/mermaid-config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    return 'diagrams/mermaid-config.json'

def convert_to_images(mmd_files, config_file):
    """Convert .mmd files to PNG images using Mermaid CLI."""
    converted_files = []
    
    # Try to find mmdc command
    mmdc_paths = [
        'mmdc',  # If in PATH
        r'C:\Users\frind\AppData\Roaming\npm\mmdc.cmd',  # Windows npm global
        'npx mmdc'  # Using npx
    ]
    
    mmdc_cmd = None
    for path in mmdc_paths:
        try:
            if path == 'npx mmdc':
                test_cmd = ['npx', 'mmdc', '--help']
            else:
                test_cmd = [path, '--help']
            subprocess.run(test_cmd, capture_output=True, check=True)
            mmdc_cmd = path
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not mmdc_cmd:
        print("✗ Error: Could not find mmdc command. Trying alternative approach...")
        return create_images_with_node(mmd_files, config_file)
    
    print(f"Using mmdc command: {mmdc_cmd}")
    
    for mmd_file in mmd_files:
        png_file = mmd_file.with_suffix('.png')
        
        # Use mmdc (Mermaid CLI) to convert
        if mmdc_cmd == 'npx mmdc':
            cmd = [
                'npx', 'mmdc',
                '-i', str(mmd_file),
                '-o', str(png_file),
                '-c', config_file,
                '-w', '1200',  # Width
                '-H', '800',   # Height
                '--backgroundColor', 'white'
            ]
        else:
            cmd = [
                mmdc_cmd,
                '-i', str(mmd_file),
                '-o', str(png_file),
                '-c', config_file,
                '-w', '1200',  # Width
                '-H', '800',   # Height
                '--backgroundColor', 'white'
            ]
        
        try:
            print(f"Converting {mmd_file.name} to PNG...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            converted_files.append(png_file)
            print(f"✓ Created: {png_file}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error converting {mmd_file}: {e}")
            print(f"  stdout: {e.stdout}")
            print(f"  stderr: {e.stderr}")
        except FileNotFoundError:
            print("✗ Error: mmdc command not found. Make sure @mermaid-js/mermaid-cli is installed globally.")
            return []
    
    return converted_files

def create_diagram_readme(diagrams, output_dir):
    """Create a README file describing all the diagrams."""
    readme_content = """# Network Flow Diagrams - Visual Reference

This directory contains visual representations of the TIDAL-DL-NG network flow diagrams.

## Diagram Files

"""
    
    for i, diagram in enumerate(diagrams, 1):
        readme_content += f"### {i:02d}. {diagram['title']}\n"
        readme_content += f"- **File**: `{diagram['filename']}.png`\n"
        readme_content += f"- **Source**: `{diagram['filename']}.mmd`\n\n"
    
    readme_content += """
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
"""
    
    readme_file = Path(output_dir) / 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"Created: {readme_file}")
    return readme_file

def main():
    """Main function to extract and convert diagrams."""
    markdown_file = 'NETWORK_FLOW_DIAGRAMS.md'
    output_dir = 'diagrams'
    
    if not os.path.exists(markdown_file):
        print(f"Error: {markdown_file} not found!")
        sys.exit(1)
    
    print("Extracting Mermaid diagrams...")
    diagrams = extract_mermaid_diagrams(markdown_file)
    print(f"Found {len(diagrams)} diagrams")
    
    print("\nCreating individual .mmd files...")
    mmd_files = create_mermaid_files(diagrams, output_dir)
    
    print("\nCreating Mermaid configuration...")
    config_file = create_mermaid_config()
    
    print("\nConverting diagrams to PNG images...")
    png_files = convert_to_images(mmd_files, config_file)
    
    print("\nCreating README documentation...")
    create_diagram_readme(diagrams, output_dir)
    
    print(f"\n✓ Successfully processed {len(diagrams)} diagrams")
    print(f"✓ Created {len(mmd_files)} .mmd files")
    print(f"✓ Created {len(png_files)} PNG images")
    print(f"\nAll files are in the '{output_dir}' directory")

if __name__ == '__main__':
    main()
