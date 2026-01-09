"""
Core AccessDatabase class for MS Access database operations.
"""

from pathlib import Path

import pandas as pd
import pyodbc

from .exceptions import AccessDatabaseError, DatabaseConnectionError, TableNotFoundError
from .models import ColumnInfo, TableInfo


class AccessDatabase:
    """
    Main class for accessing MS Access databases.

    Provides methods to connect to and query MS Access databases using pyodbc.
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
        if not self.db_path.exists():
            raise DatabaseConnectionError(f"Database file not found: {db_path}")

        # Try to connect to the database using pyodbc
        try:
            conn_str = (
                r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={self.db_path};'
            )
            self._connection = pyodbc.connect(conn_str)
        except pyodbc.Error as e:
            # Check if driver is available and provide helpful error message
            self._check_driver()
            raise DatabaseConnectionError(f"Cannot access database: {db_path}. Error: {e}")

        self._tables_cache: list[str] | None = None
        self._schema_cache: dict[str, TableInfo] | None = None

    def _check_driver(self) -> None:
        """Check if Microsoft Access ODBC driver is available and provide installation instructions."""
        available_drivers = pyodbc.drivers()
        access_drivers = [d for d in available_drivers if 'Access' in d or 'access' in d]

        if not access_drivers:
            raise DatabaseConnectionError(
                "Microsoft Access ODBC driver not found.\n\n"
                "To use pyaccess, you need to install the Microsoft Access Database Engine:\n"
                "1. Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920\n"
                "2. Important: Install the version (32-bit or 64-bit) that matches your Python installation\n"
                "   - Check your Python: python -c \"import struct; print(struct.calcsize('P') * 8, 'bit')\"\n"
                "   - 32-bit Python requires 32-bit ACE driver\n"
                "   - 64-bit Python requires 64-bit ACE driver\n\n"
                f"Available ODBC drivers on your system: "
                f"{', '.join(available_drivers) if available_drivers else 'None'}"
            )

    def get_tables(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        if self._tables_cache is None:
            cursor = self._connection.cursor()
            # Get all user tables (table_type='TABLE' excludes system tables)
            tables = cursor.tables(tableType='TABLE')
            self._tables_cache = [row.table_name for row in tables if not row.table_name.startswith('MSys')]
            cursor.close()
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
        cursor = self._connection.cursor()

        for table_name in self.get_tables():
            columns = []
            # Get column information for this table
            for col in cursor.columns(table=table_name):
                # Map ODBC type codes to readable type names
                type_name = col.type_name
                nullable = col.nullable == 1

                columns.append(ColumnInfo(
                    name=col.column_name,
                    type=type_name,
                    nullable=nullable
                ))

            if columns:
                self._schema_cache[table_name] = TableInfo(name=table_name, columns=columns)

        cursor.close()

    def _convert_where_clause(self, where: str) -> str:
        """
        Convert pandas query syntax to SQL WHERE clause.

        Args:
            where: pandas-style query string (e.g., "column == 'value'" or 'column == "value"')

        Returns:
            SQL-compatible WHERE clause
        """
        # Replace pandas operators with SQL equivalents
        sql_where = where.replace('==', '=')

        # Convert double quotes to single quotes for string literals in Access SQL
        # This handles cases like: column == "value"
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

        # Get table info to validate columns
        table_info = self.get_table_info(table_name)
        valid_columns = [col.name for col in table_info.columns]

        # Build SQL query
        if columns:
            # Filter to only valid columns (for backward compatibility with mdbtools behavior)
            valid_requested_cols = [col for col in columns if col in valid_columns]

            # If no valid columns, return empty DataFrame
            if not valid_requested_cols:
                return pd.DataFrame()

            # Wrap column names in brackets for Access SQL
            col_list = ', '.join([f'[{col}]' for col in valid_requested_cols])
        else:
            col_list = '*'

        sql = "SELECT "

        # Add TOP clause for limit (Access SQL uses TOP instead of LIMIT)
        if limit:
            sql += f"TOP {limit} "

        sql += f"{col_list} FROM [{table_name}]"

        # Add WHERE clause if specified
        if where:
            sql_where = self._convert_where_clause(where)
            sql += f" WHERE {sql_where}"

        try:
            df = pd.read_sql(sql, self._connection)
            return df
        except Exception as e:
            raise AccessDatabaseError(f"Query failed: {sql}. Error: {e}")

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

        cursor = self._connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

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

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if hasattr(self, '_connection'):
            self._connection.close()
