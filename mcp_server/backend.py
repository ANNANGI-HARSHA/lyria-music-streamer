"""Pluggable model backend for the MCP server.

This module exposes `generate(prompt)` which will:
- If `GEMINI_API_KEY` and `GEMINI_API_URL` are set in the environment, POST the prompt
  to that URL with Authorization Bearer header and return the parsed JSON response (or a
  simple mapping).
- Otherwise fall back to a local dummy response (the previous behaviour).

This implementation uses only the Python standard library so no extra dependencies are
required. Configure `GEMINI_API_URL` to the correct Gemini endpoint (example below).
"""
from typing import Any, Dict
import os
import json
import urllib.request
import urllib.error


def _call_gemini(prompt: str) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    api_url = os.environ.get("GEMINI_API_URL")
    if not api_key or not api_url:
        raise RuntimeError("GEMINI_API_KEY or GEMINI_API_URL not configured")

    payload = {"prompt": prompt}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except Exception:
                # If the API returns plain text, wrap it.
                return {"output": raw}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Gemini API HTTPError: {e.code} {e.reason} - {body}")
    except Exception as e:
        raise RuntimeError(f"Failed to call Gemini API: {e}")


def generate(prompt: str) -> Dict[str, Any]:
    """Generate a response for the given prompt.

    If GEMINI_API_KEY and GEMINI_API_URL are configured, call Gemini. Otherwise return a
    local dummy response.
    """
    try:
        if os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_API_URL"):
            resp = _call_gemini(prompt)
            # Normalize possible shapes into {"output": str, "meta": {...}}
            if isinstance(resp, dict):
                if "output" in resp:
                    return {"output": resp["output"], "meta": resp.get("meta", {})}
                # Guess shape where text is under 'text' or 'result'
                for key in ("text", "result", "content"):
                    if key in resp and isinstance(resp[key], str):
                        return {"output": resp[key], "meta": resp.get("meta", {})}
                # Otherwise return stringified whole response
                return {"output": json.dumps(resp), "meta": {}}
    except Exception as e:
        # If remote call fails, fall back to dummy but include error meta.
        return {"output": f"[mcp-server-dummy-fallback] {prompt}", "meta": {"error": str(e)}}

    # Default dummy response
    return {"output": f"[mcp-server-dummy] {prompt}", "meta": {"length": len(prompt)}}
