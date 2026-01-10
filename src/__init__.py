"""
PyAccess - Python library for MS Access databases
"""

from .pyaccess import (
    AccessDatabase,
    AccessDatabaseError,
    CollarData,
    ColumnInfo,
    DatabaseConnectionError,
    GeologicalDatabase,
    LithologyData,
    SurveyData,
    TableInfo,
    TableNotFoundError,
)

__version__ = "0.1.0a4"
__all__ = [
    "AccessDatabase",
    "GeologicalDatabase",
    "AccessDatabaseError",
    "DatabaseConnectionError",
    "TableNotFoundError",
    "ColumnInfo",
    "TableInfo",
    "CollarData",
    "SurveyData",
    "LithologyData",
]
