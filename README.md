# Lyria Realtime Demo

This project runs a small Flask server that exposes a WebSocket endpoint to stream generated music (Lyria).

Prerequisites
- Python 3.8+ installed
- A Gemini API key stored in `.env` as `GEMINI_API_KEY`

Quick start (PowerShell)

1. Create a `.env` file in the project root with your API key:

```powershell
Set-Content -Path .\.env -Value "GEMINI_API_KEY=your_api_key_here"
```

2. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
python -m pip install --upgrade pip; python -m pip install -r requirements.txt
```

4. Run the server:

```powershell
python app.py
```

5. Open http://127.0.0.1:5000 in your browser and click "Connect to Server".

Troubleshooting
- If the server complains about missing packages, ensure you activated the virtual environment.
- If WebSocket connections fail, try installing/upgrading `gevent` or `eventlet` and restart the server.

Files of interest
- `index.html` — Front-end UI that connects to `/ws`
- `lyria-test-app.py` — A helper script to test direct GenAI streaming from the terminal


MCP server
----------

This repo contains a minimal local MCP server stub under `mcp_server/`.
Start it with `python -m mcp_server.server` and POST to `/mcp/infer` to test the integration during development.
Contact
If you want, I can try to install dependencies and start the server for you now. If so, tell me whether it's OK to run installation commands in the workspace environment.