"""
Mdbtools backend for MS Access database operations on Linux.
"""

import csv
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from .exceptions import AccessDatabaseError, DatabaseConnectionError, TableNotFoundError
from .models import ColumnInfo, TableInfo


class MdbtoolsAccessDatabase:
    """
    MS Access database access using mdbtools (Linux).

    This backend uses mdbtools command-line utilities to read MS Access databases
    without requiring ODBC drivers.
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize mdbtools database connection.

        Args:
            db_path: Path to the .accdb or .mdb file

        Raises:
            DatabaseConnectionError: If the database file cannot be accessed
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise DatabaseConnectionError(f"Database file not found: {db_path}")

        # Check if mdbtools is available
        try:
            result = subprocess.run(
                ["mdb-tables", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise DatabaseConnectionError("mdbtools not found or not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise DatabaseConnectionError(
                "mdbtools not found. Please install mdbtools:\n"
                "  Ubuntu/Debian: sudo apt install mdbtools\n"
                "  CentOS/RHEL: sudo yum install mdbtools\n"
                "  macOS: brew install mdbtools"
            )

        self._tables_cache: list[str] | None = None
        self._schema_cache: dict[str, TableInfo] | None = None

    def get_tables(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        if self._tables_cache is None:
            try:
                result = subprocess.run(
                    ["mdb-tables", "-1", str(self.db_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    raise AccessDatabaseError(f"Failed to get tables: {result.stderr}")

                # Filter out system tables and empty lines
                tables = [
                    line.strip()
                    for line in result.stdout.split('\n')
                    if line.strip() and not line.startswith('MSys')
                ]
                self._tables_cache = tables
            except subprocess.TimeoutExpired:
                raise AccessDatabaseError("Timeout getting table list")
            except Exception as e:
                raise AccessDatabaseError(f"Error getting tables: {e}")

        return self._tables_cache.copy()

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
        if table_name not in self.get_tables():
            raise TableNotFoundError(f"Table '{table_name}' not found")

        if self._schema_cache is None:
            self._load_schema_cache()

        return self._schema_cache[table_name]

    def _load_schema_cache(self) -> None:
        """Load and cache schema information for all tables."""
        self._schema_cache = {}

        for table_name in self.get_tables():
            # Get column information by examining the first row of data
            try:
                # Export just a few rows to get headers and sample data
                result = subprocess.run(
                    ["mdb-export", str(self.db_path), table_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    # If we can't get schema, create basic info
                    columns = [ColumnInfo(name=f"col_{i}", type="Unknown", nullable=True)
                              for i in range(self._get_table_row_count(table_name))]
                    self._schema_cache[table_name] = TableInfo(name=table_name, columns=columns)
                    continue

                # Parse CSV to get column names from header
                lines = result.stdout.strip().split('\n')
                if not lines:
                    columns = []
                else:
                    # First line is the header
                    csv_reader = csv.reader(StringIO(lines[0]), delimiter=',', quotechar='"')
                    try:
                        header_row = next(csv_reader)
                        # mdbtools doesn't provide detailed type info, so we use generic types
                        columns = [
                            ColumnInfo(name=col.strip(), type="Text", nullable=True)
                            for col in header_row
                        ]
                    except StopIteration:
                        columns = []

                self._schema_cache[table_name] = TableInfo(name=table_name, columns=columns)

            except subprocess.TimeoutExpired:
                raise AccessDatabaseError(f"Timeout loading schema for table {table_name}")
            except Exception as e:
                raise AccessDatabaseError(f"Error loading schema for table {table_name}: {e}")

    def _get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table."""
        try:
            result = subprocess.run(
                ["mdb-export", str(self.db_path), table_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                # Count lines (subtract 1 for header)
                lines = result.stdout.strip().split('\n')
                return max(0, len(lines) - 1)
        except:
            pass
        return 0

    def _convert_where_clause(self, where: str) -> str:
        """
        Convert pandas query syntax to SQL WHERE clause.

        For mdbtools, we need to handle this differently since mdb-export doesn't support WHERE.
        We'll need to filter the data after export.

        Args:
            where: pandas-style query string

        Returns:
            SQL-compatible WHERE clause (for future use)
        """
        # For now, return as-is since mdbtools export doesn't support WHERE
        # Filtering will be done in Python after data export
        sql_where = where.replace('==', '=')
        sql_where = sql_where.replace('"', "'")
        return sql_where

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
        if table_name not in self.get_tables():
            raise TableNotFoundError(f"Table '{table_name}' not found")

        try:
            # Build mdb-export command
            cmd = ["mdb-export", str(self.db_path), table_name]

            # mdb-export doesn't support column selection or WHERE clauses directly
            # We'll export all data and filter in Python

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # Allow more time for large exports
            )

            if result.returncode != 0:
                raise AccessDatabaseError(f"Failed to export table {table_name}: {result.stderr}")

            # Parse CSV output
            df = pd.read_csv(StringIO(result.stdout), quotechar='"', escapechar='\\')

            # Apply column filtering if specified
            if columns:
                table_info = self.get_table_info(table_name)
                valid_columns = [col.name for col in table_info.columns]
                valid_requested_cols = [col for col in columns if col in valid_columns]

                if not valid_requested_cols:
                    return pd.DataFrame()

                # Filter to requested columns
                df = df[valid_requested_cols]

            # Apply WHERE filtering if specified
            if where:
                try:
                    # Use pandas query syntax
                    df = df.query(where)
                except Exception as e:
                    raise AccessDatabaseError(f"Invalid WHERE clause '{where}': {e}")

            # Apply limit if specified
            if limit:
                df = df.head(limit)

            return df

        except subprocess.TimeoutExpired:
            raise AccessDatabaseError(f"Timeout querying table {table_name}")
        except Exception as e:
            raise AccessDatabaseError(f"Error querying table {table_name}: {e}")

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
        if table_name not in self.get_tables():
            raise TableNotFoundError(f"Table '{table_name}' not found")

        df = self.query_table(table_name)
        return len(df)

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
        df = self.query_table(table_name, columns=columns, where=where, limit=limit)
        df.to_csv(output_path, index=False)

    def close(self) -> None:
        """Close the database connection (no-op for mdbtools)."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()