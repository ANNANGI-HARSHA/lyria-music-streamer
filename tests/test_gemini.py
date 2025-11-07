"""Tests for Gemini API integration in backend.py."""
import json
import os
from typing import Any, Dict, Optional
from unittest.mock import patch
import urllib.error

import pytest

from mcp_server.backend import generate, _call_gemini


def mock_urlopen_factory(response_json: Dict[str, Any], *, status: int = 200):
    """Create a mock urlopen that returns the given response."""
    class MockFP:
        """Mock file-like object for HTTPError."""
        def read(self):
            return json.dumps(response_json).encode()
        def close(self):
            pass

    class MockResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            if status != 200:
                err = urllib.error.HTTPError(
                    "https://example.com", status, "Error",
                    {"Content-Type": "application/json"},
                    MockFP()
                )
                raise err
            return json.dumps(response_json).encode()
    return lambda *args, **kwargs: MockResponse()


def test_generate_uses_dummy_without_api_key():
    """Test generate() returns dummy response when GEMINI_API_KEY not set."""
    with patch.dict(os.environ, clear=True):
        result = generate("test prompt")
        assert result["output"] == "[mcp-server-dummy] test prompt"
        assert "length" in result["meta"]
        assert result["meta"]["backend"] == "dummy"


def test_generate_respects_use_dummy():
    """Test generate(use_dummy=True) returns dummy even with API key."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}):
        result = generate("test", use_dummy=True)
        assert result["output"] == "[mcp-server-dummy] test"
        assert result["meta"]["backend"] == "dummy"


def test_call_gemini_formats_request_correctly():
    """Test _call_gemini sends properly formatted request to Gemini API."""
    mock_response = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "mock response"
                }]
            }
        }]
    }

    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_key",
        "GEMINI_API_URL": "https://example.com/generate"
    }), patch("urllib.request.urlopen", mock_urlopen_factory(mock_response)):
        result = _call_gemini("test prompt", temperature=0.5)

        assert result["output"] == "mock response"
        assert result["meta"]["model"] == "gemini-pro"
        assert result["meta"]["temperature"] == 0.5


def test_call_gemini_handles_error():
    """Test _call_gemini handles API errors gracefully."""
    error_response = {"error": {"message": "Invalid request"}}
    
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_key"
    }), patch("urllib.request.urlopen", mock_urlopen_factory(error_response, status=400)):
        with pytest.raises(RuntimeError) as excinfo:
            _call_gemini("test prompt")
        assert "HTTPError: 400" in str(excinfo.value)


def test_generate_falls_back_on_error():
    """Test generate() falls back to dummy on API error but includes error info."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_key"
    }), patch("urllib.request.urlopen", mock_urlopen_factory({}, status=500)):
        result = generate("test prompt")
        assert "[mcp-server-dummy-fallback]" in result["output"]
        assert "error" in result["meta"]
        assert result["meta"]["backend"] == "gemini-pro"