"""
Core AccessDatabase class for MS Access database operations.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from .exceptions import AccessDatabaseError, DatabaseConnectionError, TableNotFoundError
from .models import ColumnInfo, TableInfo


class AccessDatabase:
    """
    Main class for accessing MS Access databases.

    Provides methods to connect to and query MS Access databases using mdbtools.
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

        # Verify we can access the database
        try:
            self._run_mdb_command(["mdb-tables", str(self.db_path)])
        except subprocess.CalledProcessError:
            raise DatabaseConnectionError(f"Cannot access database: {db_path}")

        self._tables_cache: list[str] | None = None
        self._schema_cache: dict[str, TableInfo] | None = None

    def _run_mdb_command(self, command: list[str]) -> str:
        """Run an mdbtools command and return the output."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise AccessDatabaseError(f"mdbtools command failed: {e.stderr}")

    def get_tables(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        if self._tables_cache is None:
            output = self._run_mdb_command(["mdb-tables", str(self.db_path)])
            self._tables_cache = [table.strip() for table in output.split() if table.strip()]
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

        # Get schema for all tables
        output = self._run_mdb_command(["mdb-schema", str(self.db_path)])

        current_table = None
        columns = []

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("CREATE TABLE ["):
                # New table definition
                if current_table and columns:
                    self._schema_cache[current_table] = TableInfo(name=current_table, columns=columns)

                table_name = line.split("[")[1].split("]")[0]
                current_table = table_name
                columns = []
            elif line.startswith("[") and "]" in line and current_table:
                # Column definition
                col_def = line.strip("(),;")
                parts = col_def.split("\t")

                if len(parts) >= 2:
                    col_name = parts[0].strip("[]")
                    col_type = parts[1].strip()
                    nullable = "NOT NULL" not in col_def

                    columns.append(ColumnInfo(name=col_name, type=col_type, nullable=nullable))

        # Add the last table
        if current_table and columns:
            self._schema_cache[current_table] = TableInfo(name=current_table, columns=columns)

    def query_table(
        self, table_name: str, columns: list[str] | None = None, where: str | None = None, limit: int | None = None
    ) -> pd.DataFrame:
        """
        Query a table and return results as a pandas DataFrame.

        Args:
            table_name: Name of the table to query
            columns: List of column names to select (None for all columns)
            where: WHERE clause (SQL syntax, without the WHERE keyword)
            limit: Maximum number of rows to return

        Returns:
            pandas DataFrame with query results

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        if table_name not in self.get_tables():
            raise TableNotFoundError(f"Table '{table_name}' not found")

        # Build mdb-export command
        cmd = ["mdb-export", str(self.db_path), table_name]

        # Add column selection if specified
        if columns:
            # mdb-export doesn't support column selection directly,
            # we'll filter after export
            pass

        # Execute query
        output = self._run_mdb_command(cmd)

        # Parse CSV output
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as f:
            f.write(output)
            temp_file = f.name

        try:
            df = pd.read_csv(temp_file, sep=",", quotechar='"', escapechar="\\")

            # Filter columns if specified
            if columns:
                available_cols = [col for col in columns if col in df.columns]
                df = df[available_cols]

            # Apply WHERE filtering if specified
            if where:
                # Simple WHERE clause parsing - for complex queries, would need more work
                # For now, just evaluate as pandas query
                try:
                    df = df.query(where)
                except Exception as e:
                    raise AccessDatabaseError(f"Invalid WHERE clause: {where} - {e}")

            # Apply limit
            if limit:
                df = df.head(limit)

            return df

        finally:
            os.unlink(temp_file)

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
        _ = self.query_table(table_name, limit=0)  # Just get structure
        # For count, we need to actually count rows
        df_full = self.query_table(table_name)
        return len(df_full)

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
        pass  # No cleanup needed for mdbtools
