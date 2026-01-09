"""
Collar data access for geological databases.
"""

import pandas as pd

from ..core import AccessDatabase


class CollarData:
    """Represents collar data from geological drilling."""

    def __init__(self, db: AccessDatabase):
        self.db = db

    def get_all_holes(self) -> pd.DataFrame:
        """Get all drill hole collar data."""
        return self.db.query_table("collar")

    def get_hole_by_id(self, hole_id: str) -> pd.Series | None:
        """Get collar data for a specific hole ID."""
        df = self.db.query_table("collar", where=f"hole_id == '{hole_id}'")
        if len(df) > 0:
            return df.iloc[0]
        return None

    def get_holes_in_block(self, block: str) -> pd.DataFrame:
        """Get all holes in a specific block."""
        return self.db.query_table("collar", where=f"block == '{block}'")
