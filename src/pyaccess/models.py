"""
Data models for PyAccess database structures.
"""

from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    type: str
    nullable: bool = True


@dataclass
class TableInfo:
    """Information about a database table."""

    name: str
    columns: list[ColumnInfo]
    row_count: int | None = None
