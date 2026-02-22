"""Unit tests for the CLI entry point (app/__main__.py)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def _isolate_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide deterministic settings for __main__ tests."""
    fake = type(
        "FakeSettings",
        (),
        {"host": "127.0.0.1", "port": 7777, "debug": True},
    )()
    monkeypatch.setattr("app.__main__.settings", fake)


@pytest.mark.usefixtures("_isolate_settings")
class TestMainEntry:
    @patch("app.__main__.uvicorn.run")
    def test_main_calls_uvicorn_run(self, mock_run: Any) -> None:
        """main() should call uvicorn.run exactly once."""
        from app.__main__ import main

        main()
        mock_run.assert_called_once()

    @patch("app.__main__.uvicorn.run")
    def test_main_passes_app_import_string(self, mock_run: Any) -> None:
        """main() should pass 'app.main:app' as the first argument."""
        from app.__main__ import main

        main()
        args, _ = mock_run.call_args
        assert args[0] == "app.main:app"

    @patch("app.__main__.uvicorn.run")
    def test_main_passes_host_from_settings(self, mock_run: Any) -> None:
        """main() should pass settings.host to uvicorn."""
        from app.__main__ import main

        main()
        _, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"

    @patch("app.__main__.uvicorn.run")
    def test_main_passes_port_from_settings(self, mock_run: Any) -> None:
        """main() should pass settings.port to uvicorn."""
        from app.__main__ import main

        main()
        _, kwargs = mock_run.call_args
        assert kwargs["port"] == 7777

    @patch("app.__main__.uvicorn.run")
    def test_main_passes_reload_from_debug(self, mock_run: Any) -> None:
        """main() should pass settings.debug as the reload flag."""
        from app.__main__ import main

        main()
        _, kwargs = mock_run.call_args
        assert kwargs["reload"] is True

    @patch("app.__main__.uvicorn.run")
    def test_main_reload_false_when_not_debug(
        self, mock_run: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """reload should be False when settings.debug is False."""
        fake = type(
            "FakeSettings",
            (),
            {"host": "0.0.0.0", "port": 6000, "debug": False},  # noqa: S104
        )()
        monkeypatch.setattr("app.__main__.settings", fake)

        from app.__main__ import main

        main()
        _, kwargs = mock_run.call_args
        assert kwargs["reload"] is False
