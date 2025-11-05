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

Gemini integration
------------------

This server can call a real Gemini (or other) model backend when two environment variables are set:

- `GEMINI_API_KEY` — your API key/token
- `GEMINI_API_URL` — the HTTP endpoint to POST to (example: your provider's inference endpoint)

When both are present the server will POST JSON {"prompt": "..."} to `GEMINI_API_URL` with
an Authorization: Bearer header and return the response. If the remote call fails the server
falls back to a dummy response and returns error information in the response `meta` field.

Example (PowerShell):

```powershell
Set-Content -Path .\.env -Value "GEMINI_API_KEY=your_key_here`nGEMINI_API_URL=https://your-gemini-endpoint.example/v1/infer"
python -m mcp_server.server
```

Note: you are responsible for providing the correct `GEMINI_API_URL` for your account/region.
