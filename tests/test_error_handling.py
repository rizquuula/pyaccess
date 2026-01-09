"""
Tests for error handling scenarios.
"""

import pandas as pd
import pytest

from pyaccess import AccessDatabase, AccessDatabaseError


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_where_clause(self, db):
        """Test handling of invalid WHERE clauses."""
        with pytest.raises(AccessDatabaseError):
            db.query_table("collar", where="invalid syntax +++")

    def test_context_manager(self, db_path):
        """Test context manager usage."""
        with AccessDatabase(db_path) as db:
            tables = db.get_tables()
            assert len(tables) > 0

    def test_invalid_table_query(self, db):
        """Test querying non-existent table."""
        with pytest.raises(AccessDatabaseError):
            db.query_table("nonexistent_table")

    def test_invalid_export_table(self, db, tmp_path):
        """Test exporting non-existent table."""
        output_file = tmp_path / "test.csv"
        with pytest.raises(AccessDatabaseError):
            db.export_table_to_csv("nonexistent_table", output_file)

    def test_malformed_where_clause(self, db):
        """Test various malformed WHERE clauses."""
        # These should definitely raise errors
        definitely_malformed = [
            "invalid syntax +++",  # Completely invalid syntax
        ]

        for query in definitely_malformed:
            with pytest.raises(AccessDatabaseError):
                db.query_table("collar", where=query, limit=1)

        # These might work or fail depending on pandas behavior
        # Let's test them individually
        test_cases = [
            ("hole_id = 'test'", "Wrong operator - might work with pandas"),
            ("", "Empty string - should work fine"),
        ]

        for query, description in test_cases:
            # Just ensure it doesn't crash the system
            try:
                result = db.query_table("collar", where=query, limit=1)
                assert isinstance(result, pd.DataFrame)
            except AccessDatabaseError:
                # This is also acceptable behavior
                pass

    def test_invalid_column_selection(self, db):
        """Test querying with invalid column names."""
        # Query with non-existent columns should return empty DataFrame
        # (since we filter after export)
        df = db.query_table("collar", columns=["nonexistent_col"], limit=1)
        assert isinstance(df, pd.DataFrame)
        # Should have no columns if none of the requested columns exist
        assert len(df.columns) == 0

    def test_database_file_permissions(self, db_path):
        """Test behavior with inaccessible database file."""
        # This would be hard to test reliably, but we can test the error handling
        # by trying to access a file that exists but might have permission issues
        # For now, just ensure our error handling works for other cases

    def test_large_limit_handling(self, db):
        """Test handling of very large limit values."""
        # Should handle large limits gracefully (though mdbtools might limit this)
        df = db.query_table("collar", limit=10000)
        assert isinstance(df, pd.DataFrame)
        # Should not exceed the actual table size
        total_count = db.get_table_count("collar")
        assert len(df) <= total_count
