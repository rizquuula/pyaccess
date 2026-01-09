"""
Lithology data access for geological databases.
"""

import pandas as pd

from ..core import AccessDatabase


class LithologyData:
    """Represents lithology data from geological drilling."""

    def __init__(self, db: AccessDatabase):
        self.db = db

    def get_lithology_for_hole(self, hole_id: str) -> pd.DataFrame:
        """Get lithology data for a specific hole."""
        return self.db.query_table("litho", where=f"hole_id == '{hole_id}'")

    def get_lithology_by_code(self, lith_code: str) -> pd.DataFrame:
        """Get all lithology data for a specific rock code."""
        return self.db.query_table("litho", where=f"lith_code == '{lith_code}'")

    def get_all_lithology(self) -> pd.DataFrame:
        """Get all lithology data."""
        return self.db.query_table("litho")
