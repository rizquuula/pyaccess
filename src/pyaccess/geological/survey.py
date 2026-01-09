"""
Survey data access for geological databases.
"""

import pandas as pd

from ..core import AccessDatabase


class SurveyData:
    """Represents survey data from geological drilling."""

    def __init__(self, db: AccessDatabase):
        self.db = db

    def get_survey_for_hole(self, hole_id: str) -> pd.DataFrame:
        """Get survey data for a specific hole."""
        return self.db.query_table("survey", where=f"hole_id == '{hole_id}'")

    def get_all_surveys(self) -> pd.DataFrame:
        """Get all survey data."""
        return self.db.query_table("survey")
