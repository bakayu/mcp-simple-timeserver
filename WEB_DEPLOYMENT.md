# Web Server Deployment Guide

This guide explains how to run the network-hostable version of the `mcp-simple-timeserver`. This version uses the MCP Streamable HTTP transport and is ideal for deployments where clients connect over a network.

## Overview

The web server is a stateless service that exposes two tools:
-   `get_server_time`: Returns the local time of the server machine.
-   `get_utc`: Returns the current UTC time from an NTP server.

It runs as an ASGI application using Uvicorn.

## Local Development

### 1. Install Dependencies

First, ensure you have a virtual environment set up and the base dependencies installed:

```bash
python3 -m venv venv
venv/bin/pip install -e .
```

Then, install the web-specific dependencies:
```bash
venv/bin/pip install -e '.[web]'
```
*Note: As of the current version, these dependencies (`uvicorn`, `starlette`) are already included by the core `mcp` package, but this command ensures they are present.*

### 2. Run the Server

To give more control over deployment, the server script (`mcp_simple_timeserver/web/server.py`) only defines the application but does not run it. You must use an ASGI server like `uvicorn` to run it:

```bash
venv/bin/uvicorn mcp_simple_timeserver.web.server:app --host 127.0.0.1 --port 8000
```
This will start the server on `http://127.0.0.1:8000`.

### 3. Test the Server

You can test the running server from your command line using `curl`.

**Initialize Request:**
```bash
curl -X POST http://127.0.0.1:8000/mcp/ \
-H "Content-Type: application/json" \
-H "Accept: application/json, text/event-stream" \
-d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test-client","version":"1.0"},"capabilities":{}}}'
```

**Tool Call Request (`get_server_time`):**
```bash
curl -X POST http://127.0.0.1:8000/mcp/ \
-H "Content-Type: application/json" \
-H "Accept: application/json, text/event-stream" \
-d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_server_time","arguments":{}}}'
```

## Docker Deployment

The project includes a `Dockerfile.web` for easy containerization.

### 1. Build the Docker Image

```bash
docker build -f Dockerfile.web -t mcp-simple-timeserver:web .
```

### 2. Run the Docker Container

To run the container for use with a local reverse proxy (like Apache or Nginx), you should map the container's port only to the host's loopback interface:

```bash
docker run -d -p 127.0.0.1:8000:8000 --name timeserver-web mcp-simple-timeserver:web
```
This command does two important things:
1.  It runs the container in detached mode (`-d`).
2.  It maps port 8000 inside the container to port 8000 on the **host machine's localhost interface only** (`-p 127.0.0.1:8000:8000`).

This ensures the server is not directly accessible from the network, which is the recommended setup when placing it behind a reverse proxy. The server will be accessible at `http://127.0.0.1:8000` on the host machine.

### Changing the Port

The server is configured to run on port 8000 inside the container. While you shouldn't change the internal port without rebuilding the image, you can easily change which port it's mapped to on your host machine.

**Local Development:**

To run the server on a different port locally, change the `--port` argument for `uvicorn`:
```bash
# Run on port 8080
venv/bin/uvicorn mcp_simple_timeserver.web.server:app --host 127.0.0.1 --port 8080
```

**Docker Deployment:**

To map the container to a different host port, change the first value in the `-p` parameter. The format is `-p <host_port>:<container_port>`.

```bash
# Map container's port 8000 to host's port 9000
docker run -d -p 127.0.0.1:9000:8000 --name timeserver-web mcp-simple-timeserver:web
```

The server will now be accessible at `http://127.0.0.1:9000` on the host. 

Also you can set the restart  policy to "always" - this way the container will run after reboots.

```bash

docker run -d --restart always -p 127.0.0.1:8001:8000 --name timeserver-web mcp-simple-timeserver:web
```
