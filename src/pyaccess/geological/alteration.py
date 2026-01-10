"""
Alteration data access for geological databases.
"""

import pandas as pd

from ..core import AccessDatabase


class AlterationData:
    """Represents alteration data from geological drilling."""

    def __init__(self, db: AccessDatabase):
        self.db = db

    def get_alteration_for_hole(self, hole_id: str) -> pd.DataFrame:
        """Get alteration data for a specific hole."""
        return self.db.query_table("alteration", where=f"hole_id == '{hole_id}'")

    def get_alteration_by_code(self, alt_code: str) -> pd.DataFrame:
        """Get all alteration data for a specific alteration code."""
        return self.db.query_table("alteration", where=f"alt_code_rev == '{alt_code}'")

    def get_all_alteration(self) -> pd.DataFrame:
        """Get all alteration data."""
        return self.db.query_table("alteration")