"""Pytest fixtures for event bus tests."""

import os
import tempfile
from pathlib import Path

import pytest


def pytest_configure(config):
    """Set up temp DB before any imports happen.

    This runs before test collection, ensuring EVENT_BUS_DB is set before
    server.py is imported (which initializes storage at module level).
    """
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    os.environ["EVENT_BUS_DB"] = temp_db.name
    # Store path for cleanup
    config._temp_db_path = temp_db.name


def pytest_unconfigure(config):
    """Clean up temp DB after all tests."""
    if hasattr(config, "_temp_db_path"):
        Path(config._temp_db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing (per-test isolation)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def storage(temp_db):
    """Create a storage instance with a temporary database."""
    from event_bus.storage import SQLiteStorage

    return SQLiteStorage(db_path=temp_db)
