from __future__ import annotations

import os

import pytest

OLLAMA_INTEGRATION_ENABLED = os.environ.get("OLLAMA_INTEGRATION_TESTS", "").lower() in (
    "1",
    "true",
    "yes",
)

OLLAMA_MODEL = os.environ.get("OLLAMA_TEST_MODEL", "tinyllama")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip Ollama integration tests unless OLLAMA_INTEGRATION_TESTS env var is set."""
    if not OLLAMA_INTEGRATION_ENABLED:
        skip_marker = pytest.mark.skip(
            reason="Ollama integration tests disabled. Set OLLAMA_INTEGRATION_TESTS=1 to enable."
        )
        for item in items:
            if "ollama_integration" in str(item.fspath):
                item.add_marker(skip_marker)
