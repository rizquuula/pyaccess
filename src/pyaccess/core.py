"""
Core AccessDatabase class for MS Access database operations.
"""

from pathlib import Path

import pandas as pd

from .backend import create_backend
from .models import TableInfo


class AccessDatabase:
    """
    Main class for accessing MS Access databases.

    Automatically chooses the appropriate backend based on the platform:
    - Linux: Uses mdbtools
    - Windows/Mac: Uses pyodbc with Microsoft Access ODBC driver
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize database connection.

        Args:
            db_path: Path to the .accdb or .mdb file

        Raises:
            DatabaseConnectionError: If the database file cannot be accessed
        """
        self.db_path = Path(db_path)
        self._backend = create_backend(db_path)

    def get_tables(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        return self._backend.get_tables()

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
        return self._backend.get_table_info(table_name)

    def query_table(
        self,
        table_name: str,
        columns: list[str] | None = None,
        where: str | None = None,
        limit: int | None = None,
        chunksize: int | None = None,
    ) -> pd.DataFrame:
        """
        Query a table and return results as a pandas DataFrame.

        Args:
            table_name: Name of the table to query
            columns: List of column names to select (None for all columns)
            where: WHERE clause (pandas query syntax, e.g., "column == 'value'")
            limit: Maximum number of rows to return
            chunksize: If specified, read data in chunks of this size and concatenate.
                       Useful for memory-efficient processing of large tables.

        Returns:
            pandas DataFrame with query results

        Raises:
            TableNotFoundError: If table doesn't exist
            AccessDatabaseError: If query fails
        """
        return self._backend.query_table(table_name, columns, where, limit)

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
        return self._backend.get_table_count(table_name)

    def export_table_to_csv(
        self,
        table_name: str,
        output_path: str | Path,
        columns: list[str] | None = None,
        where: str | None = None,
        limit: int | None = None,
        chunksize: int | None = None,
    ) -> None:
        """
        Export a table to CSV file.

        Args:
            table_name: Name of the table to export
            output_path: Path to output CSV file
            columns: List of column names to export (None for all)
            where: WHERE clause for filtering
            limit: Maximum number of rows to export
            chunksize: If specified, write data in chunks of this size.
                       Useful for memory-efficient export of large tables.

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        return self._backend.export_table_to_csv(table_name, output_path, columns, where, limit)

    def close(self) -> None:
        """Close the database connection and dispose resources."""
        if hasattr(self._backend, "close"):
            self._backend.close()

    @property
    def _connection(self):
        """Access the backend connection (for testing)."""
        return getattr(self._backend, "_connection", None)

    @property
    def _engine(self):
        """Access the backend engine (for testing)."""
        return getattr(self._backend, "_engine", None)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
