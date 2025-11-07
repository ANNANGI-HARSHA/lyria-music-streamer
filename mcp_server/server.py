"""A minimal, dependency-free MCP server.

Exposes POST /mcp/infer which accepts JSON {"prompt": "..."}
and returns a simple JSON echo response. This is intended as a
local stub MCP server you can extend later or deploy.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import argparse
import os

from . import backend


class MCPHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_POST(self):
        if self.path != "/mcp/infer":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid json"}).encode())
            return

        prompt = payload.get("prompt", "")

        # Use the pluggable backend (Gemini if configured, otherwise dummy)
        try:
            gen = backend.generate(prompt)
            if isinstance(gen, dict) and "output" in gen:
                result = gen
            else:
                result = {"output": str(gen), "meta": {}}
            status = 200
        except Exception as e:
            result = {"error": "backend_error", "details": str(e)}
            status = 500

        self._set_headers(status)
        self.wfile.write(json.dumps(result).encode())

    def log_message(self, format, *args):
        # override to keep logs minimal
        print("[mcp-server] %s - - %s" % (self.address_string(), format % args))


def run(host: str = "127.0.0.1", port: int = 3333):
    server = HTTPServer((host, port), MCPHandler)
    print(f"MCP server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down MCP server")
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run minimal MCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3333)
    args = parser.parse_args()
    run(args.host, args.port)
