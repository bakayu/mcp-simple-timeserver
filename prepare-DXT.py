#!/usr/bin/env python3
"""
DXT Packaging Script for MCP Simple Time Server (Venv Bundling Method)

This script automates the process of packaging the stdio version of the
mcp-simple-timeserver into a .dxt file for distribution. It creates a
self-contained package by bundling a full Python virtual environment.
"""

import os
import shutil
import json
import zipfile
import tomllib
import subprocess
import sys

# --- Configuration ---
BUILD_DIR = "dxt_build"
PYPROJECT_PATH = "pyproject.toml"
SOURCE_SERVER_PATH = os.path.join("mcp_simple_timeserver", "server.py")
SOURCE_ICON_PATH = "icon.png"
# ---

def create_dxt_package():
    """
    Reads configuration, builds a full virtual environment, assembles the
    DXT structure, and zips it into the final .dxt file.
    """
    print("Starting DXT packaging process with venv bundling...")

    # 1. Read metadata from pyproject.toml
    print(f"Reading metadata from {PYPROJECT_PATH}...")
    try:
        with open(PYPROJECT_PATH, "rb") as f:
            pyproject_data = tomllib.load(f)
        
        project_meta = pyproject_data["project"]
        project_name = project_meta["name"]
        project_version = project_meta["version"]
        project_description = project_meta["description"]
        # Get the full author object and add the URL
        project_author = project_meta["authors"][0]
        project_author['url'] = "https://mcp.andybrandt.net/"
        dependencies = project_meta.get("dependencies", [])
        homepage_url = project_meta.get("urls", {}).get("Homepage", "")
        # Parse license from classifiers, default to MIT
        license_str = "MIT"
        for classifier in project_meta.get("classifiers", []):
            if "License :: OSI Approved" in classifier:
                license_str = classifier.split("::")[-1].strip().replace(" License", "")
        python_version_req = project_meta.get("requires-python", ">=3.11")

    except (FileNotFoundError, KeyError) as e:
        print(f"Error: Could not read {PYPROJECT_PATH} or it is malformed. {e}")
        return

    output_filename = f"{project_name}.dxt"

    # 2. Clean up previous builds
    print("Cleaning up previous build artifacts...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(output_filename):
        os.remove(output_filename)

    # 3. Set up build directories
    print(f"Creating build directory: {BUILD_DIR}")
    server_dir = os.path.join(BUILD_DIR, "server")
    os.makedirs(server_dir)
    venv_dir = os.path.join(server_dir, "venv")

    # 4. Create and populate the virtual environment
    print(f"Creating virtual environment in '{venv_dir}'...")
    subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True, capture_output=True)

    venv_python_executable = os.path.join(venv_dir, "Scripts" if os.name == 'nt' else "bin", "python")
    
    print(f"Installing dependencies into venv using '{venv_python_executable}'...")
    install_command = [venv_python_executable, "-m", "pip", "install"] + dependencies
    subprocess.run(install_command, check=True, capture_output=True)

    # Determine the site-packages path for the manifest's PYTHONPATH
    # On Windows, packages are in 'Lib', not 'Lib/site-packages' for this setup.
    # CRITICAL: All paths in the manifest MUST use forward slashes.
    if os.name == 'nt':
        python_path_in_manifest = "${__dirname}/server/venv/Lib"
        mcp_command_path = "${__dirname}/server/venv/Scripts/python"
    else:
        # For macOS and Linux, it's typically '.../lib/pythonX.Y/site-packages'
        site_packages_cmd = [
            venv_python_executable, "-c",
            "import sysconfig; print(sysconfig.get_path('purelib'))"
        ]
        result = subprocess.run(site_packages_cmd, check=True, capture_output=True, text=True)
        abs_site_packages_path = result.stdout.strip()
        rel_site_packages_path = os.path.relpath(abs_site_packages_path, BUILD_DIR)
        python_path_in_manifest = os.path.join("${__dirname}", rel_site_packages_path).replace(os.sep, '/')
        mcp_command_path = "${__dirname}/server/venv/bin/python"

    # 5. Create manifest.json
    print("Generating manifest.json...")
    manifest_data = {
        "dxt_version": "1.0",
        "name": "MCP Simple Time Server",
        "version": project_version,
        "author": project_author,
        "description": project_description,
        "repository": {
            "type": "git",
            "url": homepage_url
        },
        "homepage": homepage_url,
        "documentation": homepage_url,
        "support": f"{homepage_url}/issues" if homepage_url else "",
        "license": license_str,
        "keywords": ["time", "ntp", "mcp", "server", "utility"],
        "compatibility": {
            "claude_desktop": ">=0.10.0",
            "platforms": ["darwin", "win32", "linux"],
            "runtimes": {
                "python": python_version_req
            }
        },
        "server": {
            "type": "python",
            "entry_point": "server/main.py",
            "mcp_config": {
                "command": mcp_command_path,
                "args": ["-u", "${__dirname}/server/main.py"],
                "env": {
                    "PYTHONPATH": python_path_in_manifest
                }
            }
        },
        "tools": [
            {
                "name": "get_local_time",
                "description": "Returns the current local time and timezone information from the local machine."
            },
            {
                "name": "get_utc",
                "description": "Returns accurate UTC time from an NTP server."
            }
        ],
        "icon": "icon.png"
    }
    manifest_path = os.path.join(BUILD_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 6. Copy server code and icon
    print("Copying server code and icon...")
    shutil.copy(SOURCE_SERVER_PATH, os.path.join(server_dir, "main.py"))
    shutil.copy(SOURCE_ICON_PATH, os.path.join(BUILD_DIR, "icon.png"))
    
    # The script no longer creates the archive. It only prepares the directory.
    # The official DXT CLI will handle the packaging in the CI/CD workflow.
    
    print("-" * 30)
    print(f"[SUCCESS] Successfully prepared the build directory: {BUILD_DIR}")
    print("-" * 30)

if __name__ == "__main__":
    create_dxt_package() 