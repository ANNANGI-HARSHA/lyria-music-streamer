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

Gemini Integration
------------------

The server can call Google's Gemini Pro model when `GEMINI_API_KEY` is set in your environment:

```powershell
# Set your API key in .env
Set-Content -Path .\.env -Value "GEMINI_API_KEY=your_key_here"

# Start the server
python -m mcp_server.server
```

The server will POST to Gemini with this format:
```json
{
    "contents": [{
        "parts": [{
            "text": "your prompt here"
        }]
    }],
    "generationConfig": {
        "temperature": 0.7,
        "candidateCount": 1
    }
}
```

Expected response format:
```json
{
    "candidates": [{
        "content": {
            "parts": [{
                "text": "generated response"
            }]
        }
    }]
}
```

MCP server response format (both Gemini and dummy modes):
```json
{
    "output": "the generated text",
    "meta": {
        "model": "gemini-pro",  # or "dummy" for local mode
        "temperature": 0.7,     # if using Gemini
        "backend": "gemini-pro" # or "dummy"
        # other response metadata
    }
}
```

You can optionally override the API endpoint by setting `GEMINI_API_URL` (default: generativelanguage.googleapis.com).

Notes:
- Temperature can be customized by adding `"temperature": 0.1` to your `/mcp/infer` POST.
- If the Gemini API call fails, the server falls back to dummy mode and includes error details in meta.
- Use `"use_dummy": true` in your POST to force dummy mode (useful for testing).
