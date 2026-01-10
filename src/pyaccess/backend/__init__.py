"""
Backend module for PyAccess database operations.

This module provides different backend implementations for accessing MS Access databases
on different platforms, with a unified interface through the AccessBackend base class.
"""

import platform
from pathlib import Path

from .base import AccessBackend

__all__ = [
    "AccessBackend",
    "create_backend",
]


def create_backend(db_path: str | Path) -> AccessBackend:
    """
    Create the appropriate backend for the current platform.

    Args:
        db_path: Path to the .accdb or .mdb file

    Returns:
        An instance of the appropriate backend class

    Raises:
        DatabaseConnectionError: If no suitable backend can be created
    """
    system = platform.system().lower()

    if system == "linux" or system == "darwin":
        # Use mdbtools on Linux and macOS
        from .mdbtools_backend import MdbtoolsBackend
        return MdbtoolsBackend(db_path)
    else:
        # Use pyodbc on Windows
        from .pyodbc_backend import PyodbcBackend
        return PyodbcBackend(db_path)
