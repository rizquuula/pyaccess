"""
Geological database class with specialized functionality.
"""

from pathlib import Path

import pandas as pd

from ..core import AccessDatabase
from .collar import CollarData
from .lithology import LithologyData
from .survey import SurveyData


class GeologicalDatabase(AccessDatabase):
    """
    Specialized database class for geological data.

    Provides convenient access to geological tables with domain-specific methods.
    """

    def __init__(self, db_path: str | Path):
        super().__init__(db_path)

        # Initialize geological data accessors
        self.collar = CollarData(self)
        self.survey = SurveyData(self)
        self.lithology = LithologyData(self)

    def get_complete_hole_data(self, hole_id: str) -> dict[str, pd.DataFrame]:
        """
        Get all data for a complete drill hole.

        Args:
            hole_id: The hole identifier

        Returns:
            Dictionary with collar, survey, and lithology data
        """
        return {
            "collar": self.collar.get_hole_by_id(hole_id),
            "survey": self.survey.get_survey_for_hole(hole_id),
            "lithology": self.lithology.get_lithology_for_hole(hole_id),
        }

    def export_hole_to_csv(self, hole_id: str, output_dir: str | Path) -> None:
        """
        Export all data for a drill hole to CSV files.

        Args:
            hole_id: The hole identifier
            output_dir: Directory to save CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        data = self.get_complete_hole_data(hole_id)

        if data["collar"] is not None:
            pd.DataFrame([data["collar"]]).to_csv(output_path / f"{hole_id}_collar.csv", index=False)

        data["survey"].to_csv(output_path / f"{hole_id}_survey.csv", index=False)

        data["lithology"].to_csv(output_path / f"{hole_id}_lithology.csv", index=False)
