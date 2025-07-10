#!/usr/bin/env python3
"""
DXT Packaging Script for MCP Simple Time Server

This script automates the process of packaging the stdio version of the
mcp-simple-timeserver into a .dxt file for distribution.
It reads metadata from pyproject.toml and assembles the package according
to the DXT specification.
"""

import os
import shutil
import json
import zipfile
import tomllib  # For Python 3.11+
import subprocess

# --- Configuration ---
BUILD_DIR = "dxt_build"
PYPROJECT_PATH = "pyproject.toml"
SOURCE_SERVER_PATH = os.path.join("mcp_simple_timeserver", "server.py")
SOURCE_ICON_PATH = "icon.png"
# ---

def create_dxt_package():
    """
    Reads configuration, builds the DXT structure in a temporary directory,
    and then zips it into the final .dxt file.
    """
    print("Starting DXT packaging process...")

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
        dependencies = project_meta["dependencies"]

        # --- Extract additional metadata ---
        homepage_url = project_meta.get("urls", {}).get("Homepage", "")
        # Parse license from classifiers, default to MIT
        license_str = "MIT"
        for classifier in project_meta.get("classifiers", []):
            if "License :: OSI Approved" in classifier:
                license_str = classifier.split("::")[-1].strip().replace(" License", "")
        python_version_req = project_meta.get("requires-python", ">=3.11")
        # ---
        
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

    # 4. Install dependencies into a 'lib' directory
    print("Installing dependencies into the 'lib' directory...")
    lib_dir = os.path.join(BUILD_DIR, "lib")
    os.makedirs(lib_dir)
    try:
        # Use pip to install dependencies into the target lib directory
        install_args = ["pip", "install"] + dependencies + ["--target", lib_dir]
        result = subprocess.run(install_args, check=True, capture_output=True, text=True)
        print(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("Error: Failed to install dependencies using pip.")
        if isinstance(e, subprocess.CalledProcessError):
            print(f"pip stdout: {e.stdout}")
            print(f"pip stderr: {e.stderr}")
        else:
            print("Could not find 'pip'. Is it installed and in your PATH?")
        return

    # Post-install fix for pywin32 on Windows
    if os.name == 'nt':
        print("Applying pywin32 post-install fix for vendored library...")
        pywin32_system32_dir = os.path.join(lib_dir, "pywin32_system32")
        win32_dir = os.path.join(lib_dir, "win32")

        if os.path.exists(pywin32_system32_dir) and os.path.exists(win32_dir):
            print(f"Copying DLLs from {pywin32_system32_dir}...")
            for dll_file in os.listdir(pywin32_system32_dir):
                if not dll_file.lower().endswith('.dll'):
                    continue
                
                src_path = os.path.join(pywin32_system32_dir, dll_file)
                base_name = os.path.splitext(dll_file)[0]
                
                # Handle special modules that go in the lib root with generic names
                if base_name.lower().startswith('pywintypes'):
                    dest_path = os.path.join(lib_dir, 'pywintypes.pyd')
                elif base_name.lower().startswith('pythoncom'):
                    dest_path = os.path.join(lib_dir, 'pythoncom.pyd')
                # Other modules go into the win32 directory
                else:
                    dest_path = os.path.join(win32_dir, base_name + '.pyd')
                
                print(f"Copying {src_path} to {dest_path}")
                shutil.copy(src_path, dest_path)
        else:
            print(f"Warning: Could not find 'pywin32_system32' or 'win32' directory. Cannot apply pywin32 fix.")

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
                "command": "python",
                "args": ["-u", "${__dirname}/server/main.py"],
                "env": {
                    "PYTHONPATH": "${__dirname}/lib"
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
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    # 6. Copy server code
    print(f"Copying server code to {server_dir}...")
    dest_server_path = os.path.join(server_dir, "main.py")
    shutil.copy(SOURCE_SERVER_PATH, dest_server_path)

    # 7. Copy icon
    print("Copying icon...")
    if os.path.exists(SOURCE_ICON_PATH):
        shutil.copy(SOURCE_ICON_PATH, os.path.join(BUILD_DIR, "icon.png"))
    else:
        print(f"Warning: Icon file not found at '{SOURCE_ICON_PATH}'. The package will be created without an icon.")

    # 8. Create the .dxt (ZIP) archive
    print(f"Creating DXT archive: {output_filename}...")
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                archive_path = os.path.relpath(file_path, BUILD_DIR)
                zipf.write(file_path, archive_path)
    
    # 9. Final cleanup
    print(f"Cleaning up build directory: {BUILD_DIR}...")
    shutil.rmtree(BUILD_DIR)

    print("-" * 30)
    print(f"Successfully created DXT package: {output_filename}")
    print("-" * 30)


if __name__ == "__main__":
    create_dxt_package() 