#!/bin/bash

# Get the directory where this script is located and cd into it
cd "$(dirname "${BASH_SOURCE[0]}")"

# If the venv is already configured, just exec the server.
if [ -f "server/venv/.configured" ]; then
    exec server/venv/bin/python -m mcp_simple_timeserver
fi

# --- First-Time Setup Logic ---
echo "Configuring MCP Simple Time Server for first run..." >&2

# Find Python
PYTHON_EXE=$(command -v python3 || command -v python)
if [ -z "$PYTHON_EXE" ]; then
    echo "Error: Python not found in PATH" >&2
    exit 1
fi
echo "Found Python at: $PYTHON_EXE" >&2

# Update pyvenv.cfg
PYTHON_HOME=$(dirname "$PYTHON_EXE")
CONFIG_FILE="server/venv/pyvenv.cfg"
sed -i.bak "s|^home = .*|home = $PYTHON_HOME|" "$CONFIG_FILE"
rm -f "${CONFIG_FILE}.bak"

# Create marker file to skip this setup next time
echo "Configured on $(date)" > "server/venv/.configured"
echo "Configuration complete. Restarting process..." >&2

# Re-execute this script. The 'exec' replaces the current shell process,
# ensuring the new process inherits the stdio pipes correctly.
exec "$0" "$@" 