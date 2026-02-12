"""Pytest configuration for integration tests.

These tests exercise real sandbox providers (Daytona, Runloop, Modal, LangSmith).
They require provider-specific credentials and optional dependencies.

When a provider isn't configured in the environment, we skip its tests rather
than failing at fixture setup.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from langsmith import Client, get_tracing_context


def _has_daytona_config() -> bool:
    return bool(os.environ.get("DAYTONA_API_KEY"))


def _has_runloop_config() -> bool:
    return bool(os.environ.get("RUNLOOP_API_KEY"))


def _has_langsmith_config() -> bool:
    return bool(os.environ.get("LANGSMITH_API_KEY"))


def _has_modal_config() -> bool:
    # Modal can authenticate via environment variables or local config file.
    if os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET"):
        return True
    return Path("~/.modal.toml").expanduser().exists()


def _has_dependency(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    daytona_ready = _has_daytona_config() and _has_dependency("daytona")
    runloop_ready = _has_runloop_config() and _has_dependency("runloop_api_client")
    modal_ready = _has_modal_config() and _has_dependency("modal")
    langsmith_ready = _has_langsmith_config() and _has_dependency("langsmith")

    skip_daytona = pytest.mark.skip(
        reason="Daytona integration tests require DAYTONA_API_KEY and the 'daytona' package",
    )
    skip_runloop = pytest.mark.skip(
        reason="Runloop integration tests require RUNLOOP_API_KEY and the 'runloop_api_client' package",
    )
    skip_modal = pytest.mark.skip(
        reason="Modal integration tests require Modal auth and the 'modal' package",
    )
    skip_langsmith = pytest.mark.skip(
        reason="LangSmith integration tests require LANGSMITH_API_KEY and the 'langsmith' package",
    )

    for item in items:
        nodeid = item.nodeid

        # Sandbox operations are currently Daytona-only.
        if "test_sandbox_operations.py" in nodeid and not daytona_ready:
            item.add_marker(skip_daytona)
            continue

        # Sandbox factory tests include separate classes per provider.
        if "TestDaytonaIntegration" in nodeid and not daytona_ready:
            item.add_marker(skip_daytona)
        if "TestRunLoopIntegration" in nodeid and not runloop_ready:
            item.add_marker(skip_runloop)
        if "TestModalIntegration" in nodeid and not modal_ready:
            item.add_marker(skip_modal)
        if "TestLangSmithIntegration" in nodeid and not langsmith_ready:
            item.add_marker(skip_langsmith)


@pytest.fixture(scope="session", autouse=True)
def langsmith_client() -> Generator[Client | None, None, None]:
    """Create a LangSmith client if LANGSMITH_API_KEY is set.

    This fixture is session-scoped and automatically used by all tests.
    It creates a single client instance and ensures it's flushed after each test.
    """
    langsmith_api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get(
        "LANGCHAIN_API_KEY"
    )

    if langsmith_api_key:
        client = get_tracing_context()["client"] or Client()
        yield client

        # Final flush at end of session
        client.flush()
    else:
        yield None


@pytest.fixture(autouse=True)
def flush_langsmith_after_test(langsmith_client: Client) -> Generator[None, None, None]:
    """Automatically flush LangSmith client after each test."""
    yield

    # This runs after each test
    if langsmith_client is not None:
        langsmith_client.flush()
