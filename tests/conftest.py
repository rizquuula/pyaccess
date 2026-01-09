"""
Shared pytest fixtures and configuration for pyaccess tests.
"""

from pathlib import Path

import pytest

from pyaccess import AccessDatabase, GeologicalDatabase


@pytest.fixture(scope="session")
def db_path():
    """Path to the test database (shared across all tests)."""
    return Path(__file__).parent.parent / "resources" / "ilbb_all.accdb"


@pytest.fixture(scope="session")
def db(db_path):
    """AccessDatabase instance for testing (shared across all tests)."""
    return AccessDatabase(db_path)


@pytest.fixture(scope="session")
def geo_db(db_path):
    """GeologicalDatabase instance for testing (shared across all tests)."""
    return GeologicalDatabase(db_path)
