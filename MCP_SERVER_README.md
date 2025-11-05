MCP Server (local stub)
========================

This repository contains a minimal, dependency-free MCP server implementation at `mcp_server/server.py`.

Usage
-----

Start the server:

```powershell
python -m mcp_server.server --host 127.0.0.1 --port 3333
```

Send a test request:

```powershell
# using PowerShell's Invoke-RestMethod
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:3333/mcp/infer -Body (@{prompt='Hello'} | ConvertTo-Json) -ContentType 'application/json'
```

Expected response:

```json
{"output":"[mcp-server-dummy] Hello","meta":{"length":5}}
```

Notes
-----
- This is a local stub intended for development and CI testing. Replace the handler logic with real model integration as needed.
- No external Python packages are required; this uses the standard library only.
