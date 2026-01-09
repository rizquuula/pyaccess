"""
Exception classes for PyAccess database operations.
"""


class AccessDatabaseError(Exception):
    """Base exception for Access database operations."""

    pass


class DatabaseConnectionError(AccessDatabaseError):
    """Exception raised when database connection fails."""

    pass


class TableNotFoundError(AccessDatabaseError):
    """Exception raised when a requested table is not found."""

    pass
