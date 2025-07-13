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

def prepare_dxt_package():
    """Prepare the DXT package directory structure."""
    # Determine paths
    root_dir = Path(__file__).parent
    build_dir = root_dir / "dxt_build"
    server_dir = build_dir / "server"
    venv_dir = server_dir / "venv"
    
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
    shutil.copy2(root_dir / "launcher.bat", build_dir / "launcher.bat")
    shutil.copy2(root_dir / "launcher.sh", build_dir / "launcher.sh")
    
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
        "fastmcp>=0.1.0", "ntplib>=0.4.0"
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
        command = "launcher.bat"
    else:
        command = "./launcher.sh"
    
    # Create manifest
    manifest = {
        "name": "mcp-simple-timeserver",
        "description": "A simple MCP server that provides time utilities including local time, UTC time from NTP servers, and timezone information",
        "author": "Andy Brandt",
        "version": "1.1.2",
        "command": command,
        "env": {
            "PYTHONPATH": "server"
        }
    }
    
    manifest_path = build_dir / "manifest.json"
    print(f"Creating manifest.json for {system}...")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDXT package prepared in: {build_dir}")
    print(f"Platform: {system}")
    print(f"Command: {command}")
    print("\nTo create the DXT package, run:")
    print(f"  npx @anthropic-ai/dxt pack ./dxt_build mcp-simple-timeserver-{system.lower()}.dxt")
    
    return build_dir

if __name__ == "__main__":
    prepare_dxt_package() 