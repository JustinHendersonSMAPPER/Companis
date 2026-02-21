"""Ollama setup verification tests.

These tests verify that Ollama is properly installed and configured
before running the full integration test suite.
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from httpx import AsyncClient as HttpxAsyncClient

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_TEST_MODEL", "tinyllama")


@pytest.mark.asyncio
class TestOllamaSetup:
    async def test_ollama_is_running(self) -> None:
        """Verify that the Ollama server is accessible."""
        async with HttpxAsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/version")
            assert response.status_code == 200
            data = response.json()
            assert "version" in data

    async def test_model_is_available(self) -> None:
        """Verify that the test model is pulled and available."""
        async with HttpxAsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            assert response.status_code == 200
            data = response.json()
            model_names = [m["name"] for m in data.get("models", [])]
            # Check for the model name (may or may not have :latest suffix)
            found = any(
                OLLAMA_MODEL in name
                for name in model_names
            )
            assert found, (
                f"Model '{OLLAMA_MODEL}' not found. "
                f"Available models: {model_names}. "
                f"Run 'ollama pull {OLLAMA_MODEL}' to install it."
            )

    async def test_model_can_generate(self) -> None:
        """Verify that the model can generate a basic response."""
        async with HttpxAsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "Say hello in one word.",
                    "stream": False,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert len(data["response"]) > 0
