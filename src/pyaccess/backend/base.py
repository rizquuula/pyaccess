"""
Abstract base class for Access database backends.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from ..models import TableInfo


class AccessBackend(ABC):
    """
    Abstract base class for MS Access database backends.

    All backend implementations must inherit from this class and implement
    all abstract methods.
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize the backend with database path.

        Args:
            db_path: Path to the .accdb or .mdb file
        """
        self.db_path = Path(db_path)

    @abstractmethod
    def get_tables(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    def get_table_info(self, table_name: str) -> TableInfo:
        """
        Get detailed information about a table.

        Args:
            table_name: Name of the table

        Returns:
            TableInfo object with column details

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        pass

    @abstractmethod
    def query_table(
        self, table_name: str, columns: list[str] | None = None, where: str | None = None, limit: int | None = None
    ) -> pd.DataFrame:
        """
        Query a table and return results as a pandas DataFrame.

        Args:
            table_name: Name of the table to query
            columns: List of column names to select (None for all columns)
            where: WHERE clause (pandas query syntax, e.g., "column == 'value'")
            limit: Maximum number of rows to return

        Returns:
            pandas DataFrame with query results

        Raises:
            TableNotFoundError: If table doesn't exist
            AccessDatabaseError: If query fails
        """
        pass

    @abstractmethod
    def get_table_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        pass

    @abstractmethod
    def export_table_to_csv(
        self,
        table_name: str,
        output_path: str | Path,
        columns: list[str] | None = None,
        where: str | None = None,
        limit: int | None = None,
    ) -> None:
        """
        Export a table to CSV file.

        Args:
            table_name: Name of the table to export
            output_path: Path to output CSV file
            columns: List of column names to export (None for all)
            where: WHERE clause for filtering
            limit: Maximum number of rows to export

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
