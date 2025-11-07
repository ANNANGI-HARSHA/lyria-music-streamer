"""Pluggable model backend for the MCP server with Gemini integration.

This module exposes `generate(prompt)` which will:
- If `GEMINI_API_KEY` is set in the environment, POST the prompt to the Gemini Pro
  endpoint with proper request format and parse the response.
- Otherwise fall back to a local dummy response (for development/testing).

Example Gemini request:
{
    "contents": [{
        "parts": [{
            "text": "your prompt here"
        }]
    }]
}

Example Gemini response:
{
    "candidates": [{
        "content": {
            "parts": [{
                "text": "generated response"
            }]
        }
    }]
}

This implementation uses only the Python standard library. Set GEMINI_API_KEY in your
environment or .env file to enable Gemini integration.
"""
from typing import Any, Dict, Optional
import os
import json
import urllib.request
import urllib.error

# Default Gemini Pro endpoint if none specified
DEFAULT_GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"


def _call_gemini(prompt: str, *, temperature: float = 0.7) -> Dict[str, Any]:
    """Call the Gemini API with proper request format and response parsing.
    
    Args:
        prompt: The text prompt to send to Gemini
        temperature: Generation temperature (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        Dict with 'output' (generated text) and 'meta' (response details)
    
    Raises:
        RuntimeError: If API call fails or response format is invalid
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured in environment")

    api_url = os.environ.get("GEMINI_API_URL", DEFAULT_GEMINI_URL)
    if "?" not in api_url:  # Add API key as query param if not in URL
        api_url = f"{api_url}?key={api_key}"

    # Format request per Gemini API spec
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": temperature,
            "candidateCount": 1,
        }
    }
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            try:
                response = json.loads(raw)
                
                # Extract text from Gemini response format
                if (
                    "candidates" in response
                    and response["candidates"]
                    and "content" in response["candidates"][0]
                    and "parts" in response["candidates"][0]["content"]
                    and response["candidates"][0]["content"]["parts"]
                    and "text" in response["candidates"][0]["content"]["parts"][0]
                ):
                    return {
                        "output": response["candidates"][0]["content"]["parts"][0]["text"],
                        "meta": {
                            "model": "gemini-pro",
                            "temperature": temperature,
                            **response.get("promptFeedback", {}),
                        }
                    }
                else:
                    raise RuntimeError(f"Unexpected Gemini response format: {response}")
                    
            except json.JSONDecodeError:
                # If API returns non-JSON (shouldn't happen), wrap it
                return {"output": raw, "meta": {"error": "non-json-response"}}
                
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Gemini API HTTPError: {e.code} {e.reason} - {body}")
    except Exception as e:
        raise RuntimeError(f"Failed to call Gemini API: {e}")


def generate(
    prompt: str,
    *,
    temperature: Optional[float] = None,
    use_dummy: bool = False
) -> Dict[str, Any]:
    """Generate a response for the given prompt.

    If GEMINI_API_KEY is configured and use_dummy=False, calls the Gemini API.
    Otherwise returns a local dummy response.

    Args:
        prompt: Text prompt to send to the model
        temperature: Optional temperature (0.0-1.0) for generation
        use_dummy: If True, always use dummy backend (for testing)

    Returns:
        Dict with 'output' (generated text) and 'meta' (response details)
    """
    if not use_dummy and os.environ.get("GEMINI_API_KEY"):
        try:
            return _call_gemini(
                prompt,
                temperature=temperature if temperature is not None else 0.7
            )
        except Exception as e:
            # If remote call fails, fall back to dummy but include error
            return {
                "output": f"[mcp-server-dummy-fallback] {prompt}",
                "meta": {
                    "error": str(e),
                    "backend": "gemini-pro",
                }
            }

    # Default dummy response (for development/testing)
    return {
        "output": f"[mcp-server-dummy] {prompt}",
        "meta": {
            "length": len(prompt),
            "backend": "dummy",
        }
    }
