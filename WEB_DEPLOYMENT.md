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

You can run the server directly using its module path:
```bash
venv/bin/python -m mcp_simple_timeserver.web.server
```
By default, it will start on `http://127.0.0.1:8000`.

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
docker build -t mcp-simple-timeserver-web -f Dockerfile.web .
```

### 2. Run the Docker Container

```bash
docker run -d -p 8000:8000 --name timeserver-web mcp-simple-timeserver-web
```
This command runs the container in detached mode and maps port 8000 on your host to port 8000 in the container. The server will be accessible at `http://localhost:8000`. 