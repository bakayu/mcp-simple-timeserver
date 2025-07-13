#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if already configured
if [ -f "server/venv/.configured" ]; then
    exec server/venv/bin/python -m mcp_simple_timeserver
fi

echo "Configuring MCP Simple Time Server for first run..."

# Find Python - try python3 first, then python
PYTHON_EXE=$(command -v python3 || command -v python)

if [ -z "$PYTHON_EXE" ]; then
    echo "Error: Python not found in PATH" >&2
    echo "Please install Python 3.11 or later and ensure it's in your PATH" >&2
    exit 1
fi

# Get the directory containing Python
PYTHON_HOME=$(dirname "$PYTHON_EXE")

echo "Found Python at: $PYTHON_HOME"

# Check Python version
PYTHON_VERSION=$("$PYTHON_EXE" --version 2>&1 | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Check if it's at least 3.11
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "Error: Python 3.11 or later is required (found $PYTHON_VERSION)" >&2
    exit 1
fi

# Update pyvenv.cfg
CONFIG_FILE="server/venv/pyvenv.cfg"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: venv configuration file not found at $CONFIG_FILE" >&2
    exit 1
fi

# Use sed to update the home line
# Create backup for safety (works on both macOS and Linux)
sed -i.bak "s|^home = .*|home = $PYTHON_HOME|" "$CONFIG_FILE"

# Remove backup file
rm -f "${CONFIG_FILE}.bak"

# Create marker file
echo "Configured on $(date)" > "server/venv/.configured"

echo "Configuration complete. Starting server..."

# Run the server
exec server/venv/bin/python -m mcp_simple_timeserver 