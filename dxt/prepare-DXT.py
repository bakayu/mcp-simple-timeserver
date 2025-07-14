#!/usr/bin/env python3
"""
Prepare DXT package directory structure for mcp-simple-timeserver.
This script creates a directory ready to be packaged by the DXT CLI tool.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
import tomllib

def to_display_name(name: str) -> str:
    """Converts a slug-like name to a display name.
    
    Example: "mcp-simple-timeserver" -> "MCP Simple Timeserver"
    """
    parts = name.split('-')
    transformed_parts = []
    for part in parts:
        if part.lower() == 'mcp':
            transformed_parts.append('MCP')
        else:
            transformed_parts.append(part.capitalize())
    return ' '.join(transformed_parts)

def prepare_dxt_package():
    """Prepare the DXT package directory structure."""
    # Determine paths
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    build_dir = root_dir / "dxt_build"
    server_dir = build_dir / "server"
    venv_dir = server_dir / "venv"

    # Read metadata from pyproject.toml
    print("Reading metadata from pyproject.toml...")
    pyproject_path = root_dir / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        
        project_meta = pyproject_data["project"]
        project_name = project_meta["name"]
        project_version = project_meta["version"]
        project_description = project_meta["description"]
        author_info = project_meta["authors"][0]
        dependencies = project_meta.get("dependencies", [])
        homepage_url = project_meta.get("urls", {}).get("Homepage", "")
        python_version_req = project_meta.get("requires-python", ">=3.11")
        
        license_str = "MIT" # Default
        for classifier in project_meta.get("classifiers", []):
            if "License :: OSI Approved" in classifier:
                license_str = classifier.split("::")[-1].strip().replace(" License", "")

    except (FileNotFoundError, KeyError, IndexError) as e:
        print(f"Error: Could not read {pyproject_path} or it is malformed. {e}")
        sys.exit(1)
    
    # Generate display name
    display_name = to_display_name(project_name)

    # Clean previous build
    if build_dir.exists():
        print(f"Cleaning previous build directory: {build_dir}")
        shutil.rmtree(build_dir)
    
    # Create directory structure
    print("Creating DXT directory structure...")
    server_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy server files
    print("Copying server files...")
    shutil.copytree(
        root_dir / "mcp_simple_timeserver",
        server_dir / "mcp_simple_timeserver",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
    )
    
    # Copy launcher scripts
    print("Copying launcher scripts...")
    shutil.copy2(script_dir / "launcher.bat", build_dir / "launcher.bat")
    shutil.copy2(script_dir / "launcher.sh", build_dir / "launcher.sh")
    
    # Copy icon if it exists
    icon_path = script_dir / "icon.png"
    if icon_path.exists():
        shutil.copy2(icon_path, build_dir / "icon.png")
    
    # Make launcher.sh executable
    launcher_sh = build_dir / "launcher.sh"
    launcher_sh.chmod(launcher_sh.stat().st_mode | 0o755)
    
    # Create virtual environment
    print(f"Creating virtual environment in {venv_dir}...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    
    # Install dependencies
    print("Installing dependencies...")
    if platform.system() == "Windows":
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
    
    subprocess.run([
        str(pip_path), "install", "--no-cache-dir",
        *dependencies
    ], check=True)
    
    # Remove home line from pyvenv.cfg to make it relocatable
    pyvenv_cfg = venv_dir / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        print("Making virtual environment relocatable...")
        lines = pyvenv_cfg.read_text().splitlines()
        # Keep all lines except the home line - let launcher set it
        filtered_lines = [line for line in lines if not line.startswith("home = ")]
        # Add a placeholder that the launcher will replace
        filtered_lines.insert(0, "home = WILL_BE_SET_BY_LAUNCHER")
        pyvenv_cfg.write_text("\n".join(filtered_lines) + "\n")
    
    # Determine platform-specific command
    system = platform.system()
    if system == "Windows":
        entry_point = "launcher.bat"
        mcp_command = "cmd.exe"
        mcp_args = ["/c", "${__dirname}\\launcher.bat"]
    else:
        entry_point = "launcher.sh"
        mcp_command = "/bin/bash"
        mcp_args = ["${__dirname}/launcher.sh"]
    
    # Create manifest with all required DXT fields
    manifest = {
        "dxt_version": "0.1",
        "name": project_name,
        "display_name": display_name,
        "version": project_version,
        "description": project_description,
        "author": {
            "name": author_info.get("name"),
            "email": author_info.get("email"),
            "url": "https://mcp.andybrandt.net/" # DXT-specific author URL
        },
        "license": license_str,
        "homepage": homepage_url,
        "repository": {
            "type": "git",
            "url": homepage_url
        },
        "keywords": ["time", "ntp", "mcp", "server", "utility"],
        "server": {
            "type": "binary",
            "entry_point": entry_point,
            "mcp_config": {
                "command": mcp_command,
                "args": mcp_args,
                "env": {
                    "PYTHONPATH": "${__dirname}/server"
                }
            }
        },
        "tools": [
            {
                "name": "get_server_time",
                "description": "Returns the current local time and timezone from the server hosting this tool."
            },
            {
                "name": "get_utc",
                "description": "Returns accurate UTC time from an NTP server."
            }
        ],
        "compatibility": {
            "claude_desktop": ">=0.10.0",
            "platforms": ["darwin", "win32"],
            "runtimes": {
                "python": python_version_req
            }
        }
    }
    
    # Add icon if it exists
    if (build_dir / "icon.png").exists():
        manifest["icon"] = "icon.png"
    
    manifest_path = build_dir / "manifest.json"
    print(f"Creating manifest.json for {system}...")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDXT package prepared in: {build_dir}")
    print(f"Platform: {system}")
    print(f"Command: {mcp_command} {' '.join(mcp_args)}")
    print("\nTo create the DXT package, run:")
    print(f"  npx @anthropic-ai/dxt pack ./dxt_build mcp-simple-timeserver-{system.lower()}.dxt")
    
    # Write version to a file for the CI workflow to use
    (build_dir / "version.txt").write_text(project_version)

    return build_dir

if __name__ == "__main__":
    prepare_dxt_package() 