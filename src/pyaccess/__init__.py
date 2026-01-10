"""
PyAccess - Python library for MS Access databases

This library provides a Pythonic interface to read MS Access (.accdb/.mdb) databases
using mdbtools, enabling cross-platform access to Access databases on Linux.
"""

from .core import AccessDatabase
from .exceptions import AccessDatabaseError, DatabaseConnectionError, TableNotFoundError
from .geological import CollarData, GeologicalDatabase, LithologyData, SurveyData
from .models import ColumnInfo, TableInfo

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
