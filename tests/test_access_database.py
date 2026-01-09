"""
Tests for basic AccessDatabase functionality.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from pyaccess import AccessDatabase, DatabaseConnectionError, TableNotFoundError


class TestAccessDatabase:
    """Test basic AccessDatabase functionality."""

    def test_database_connection(self, db_path):
        """Test database connection."""
        db = AccessDatabase(db_path)
        assert db.db_path == db_path

    def test_invalid_database_path(self):
        """Test error handling for invalid database path."""
        with pytest.raises(DatabaseConnectionError):
            AccessDatabase("nonexistent.accdb")

    def test_get_tables(self, db):
        """Test getting table list."""
        tables = db.get_tables()
        expected_tables = ["alteration", "collar", "litho", "styles", "survey", "translation"]
        assert set(tables) == set(expected_tables)

    def test_get_table_info(self, db):
        """Test getting table information."""
        info = db.get_table_info("collar")

        # Check basic structure
        assert info.name == "collar"
        assert len(info.columns) > 0

        # Check for expected columns
        column_names = [col.name for col in info.columns]
        assert "hole_id" in column_names
        assert "x" in column_names
        assert "y" in column_names
        assert "z" in column_names

    def test_table_not_found(self, db):
        """Test error for non-existent table."""
        with pytest.raises(TableNotFoundError):
            db.get_table_info("nonexistent_table")

    def test_query_table(self, db):
        """Test basic table querying."""
        df = db.query_table("collar", limit=5)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 5
        assert "hole_id" in df.columns

    def test_query_with_columns(self, db):
        """Test querying specific columns."""
        df = db.query_table("collar", columns=["hole_id", "max_depth"], limit=3)
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"hole_id", "max_depth"}

    def test_query_with_where(self, db):
        """Test querying with WHERE clause."""
        # Get first hole ID to test with
        df_all = db.query_table("collar", limit=1)
        if len(df_all) > 0:
            hole_id = df_all.iloc[0]["hole_id"]
            df = db.query_table("collar", where=f"hole_id == '{hole_id}'")
            assert len(df) == 1
            assert df.iloc[0]["hole_id"] == hole_id

    def test_get_table_count(self, db):
        """Test getting table row count."""
        count = db.get_table_count("collar")
        assert isinstance(count, int)
        assert count >= 0

    def test_export_to_csv(self, db):
        """Test exporting table to CSV."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            db.export_table_to_csv("collar", tmp_path, limit=3)
            assert Path(tmp_path).exists()

            # Verify the exported data
            df_exported = pd.read_csv(tmp_path)
            assert len(df_exported) <= 3

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_query_with_chunksize(self, db):
        """Test querying with chunksize parameter."""
        # Query with small chunksize
        df = db.query_table("collar", chunksize=2)
        assert isinstance(df, pd.DataFrame)
        assert "hole_id" in df.columns

        # Verify result matches non-chunked query
        df_regular = db.query_table("collar")
        assert len(df) == len(df_regular)
        assert set(df.columns) == set(df_regular.columns)

    def test_query_with_chunksize_and_limit(self, db):
        """Test querying with both chunksize and limit."""
        df = db.query_table("collar", limit=5, chunksize=2)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 5

    def test_query_with_chunksize_and_where(self, db):
        """Test querying with chunksize and WHERE clause."""
        # Get first hole ID to test with
        df_all = db.query_table("collar", limit=1)
        if len(df_all) > 0:
            hole_id = df_all.iloc[0]["hole_id"]
            df = db.query_table("collar", where=f"hole_id == '{hole_id}'", chunksize=10)
            assert isinstance(df, pd.DataFrame)
            assert len(df) >= 1
            assert all(df["hole_id"] == hole_id)

    def test_query_empty_result_with_chunksize(self, db):
        """Test querying with chunksize returns empty DataFrame when no results."""
        df = db.query_table("collar", where="hole_id == 'NONEXISTENT_HOLE'", chunksize=10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_export_to_csv_with_chunksize(self, db):
        """Test exporting table to CSV with chunked writing."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            db.export_table_to_csv("collar", tmp_path, limit=10, chunksize=3)
            assert Path(tmp_path).exists()

            # Verify the exported data
            df_exported = pd.read_csv(tmp_path)
            assert len(df_exported) <= 10
            assert "hole_id" in df_exported.columns

            # Verify against non-chunked export
            df_regular = db.query_table("collar", limit=10)
            assert len(df_exported) == len(df_regular)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_export_empty_result_with_chunksize(self, db):
        """Test exporting empty result with chunksize creates file with headers."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            db.export_table_to_csv(
                "collar",
                tmp_path,
                where="hole_id == 'NONEXISTENT_HOLE'",
                chunksize=10
            )
            assert Path(tmp_path).exists()

            # Verify file has headers but no data
            df_exported = pd.read_csv(tmp_path)
            assert len(df_exported) == 0
            assert len(df_exported.columns) > 0  # Should have column headers

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_close_method(self, db_path):
        """Test close() method properly disposes resources."""
        db = AccessDatabase(db_path)
        tables = db.get_tables()
        assert len(tables) > 0

        # Close connections
        db.close()

        # After closing, _connection and _engine should be None
        assert db._connection is None
        assert db._engine is None
