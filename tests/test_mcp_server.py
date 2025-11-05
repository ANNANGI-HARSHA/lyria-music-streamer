import threading
import json
import time
import urllib.request

from http.server import HTTPServer

from mcp_server.server import MCPHandler


def test_mcp_infer_endpoint():
    # Start a temporary HTTPServer using the MCPHandler on an ephemeral port
    server = HTTPServer(("127.0.0.1", 0), MCPHandler)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://{host}:{port}/mcp/infer"
        payload = json.dumps({"prompt": "hello pytest"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)

        # Basic assertions about the response shape
        assert isinstance(data, dict)
        assert "output" in data or "error" not in data
        # If output present, ensure it's a string and contains our prompt or the dummy prefix
        if "output" in data:
            assert isinstance(data["output"], str)
            assert "hello pytest" in data["output"] or "mcp-server" in data["output"]

    finally:
        server.shutdown()
        thread.join(timeout=2)
