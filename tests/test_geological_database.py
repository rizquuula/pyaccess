"""
Tests for GeologicalDatabase specific functionality.
"""

import tempfile
from pathlib import Path

import pandas as pd


class TestGeologicalDatabase:
    """Test GeologicalDatabase specific functionality."""

    def test_collar_data_access(self, geo_db):
        """Test collar data access methods."""
        collar_df = geo_db.collar.get_all_holes()
        assert isinstance(collar_df, pd.DataFrame)
        assert len(collar_df) > 0

    def test_specific_hole_data(self, geo_db):
        """Test getting data for specific holes."""
        collar_df = geo_db.collar.get_all_holes()
        if len(collar_df) > 0:
            hole_id = collar_df.iloc[0]["hole_id"]

            # Test collar data for specific hole
            hole_data = geo_db.collar.get_hole_by_id(hole_id)
            assert hole_data is not None
            assert hole_data["hole_id"] == hole_id

            # Test survey data
            survey_data = geo_db.survey.get_survey_for_hole(hole_id)
            assert isinstance(survey_data, pd.DataFrame)

            # Test lithology data
            litho_data = geo_db.lithology.get_lithology_for_hole(hole_id)
            assert isinstance(litho_data, pd.DataFrame)

    def test_get_complete_hole_data(self, geo_db):
        """Test getting complete hole data."""
        collar_df = geo_db.collar.get_all_holes()
        if len(collar_df) > 0:
            hole_id = collar_df.iloc[0]["hole_id"]

            data = geo_db.get_complete_hole_data(hole_id)
            assert "collar" in data
            assert "survey" in data
            assert "lithology" in data

            assert data["collar"] is not None
            assert isinstance(data["survey"], pd.DataFrame)
            assert isinstance(data["lithology"], pd.DataFrame)

    def test_export_hole_to_csv(self, geo_db):
        """Test exporting hole data to CSV files."""
        collar_df = geo_db.collar.get_all_holes()
        if len(collar_df) > 0:
            hole_id = collar_df.iloc[0]["hole_id"]

            with tempfile.TemporaryDirectory() as tmp_dir:
                geo_db.export_hole_to_csv(hole_id, tmp_dir)

                # Check that files were created
                expected_files = [f"{hole_id}_collar.csv", f"{hole_id}_survey.csv", f"{hole_id}_lithology.csv"]

                for filename in expected_files:
                    assert (Path(tmp_dir) / filename).exists()

    def test_holes_in_block(self, geo_db):
        """Test getting holes in a specific block."""
        collar_df = geo_db.collar.get_all_holes()
        if len(collar_df) > 0:
            # Get a block that exists in the data
            first_block = collar_df.iloc[0]["block"]
            holes_in_block = geo_db.collar.get_holes_in_block(first_block)

            assert isinstance(holes_in_block, pd.DataFrame)
            # All returned holes should be in the specified block
            if len(holes_in_block) > 0:
                assert all(holes_in_block["block"] == first_block)

    def test_lithology_queries(self, geo_db):
        """Test various lithology query methods."""
        # Test getting all lithology data
        all_litho = geo_db.lithology.get_all_lithology()
        assert isinstance(all_litho, pd.DataFrame)

        # Test lithology by code (if there are codes in the data)
        if len(all_litho) > 0 and "lith_code" in all_litho.columns:
            unique_codes = all_litho["lith_code"].dropna().unique()
            if len(unique_codes) > 0:
                first_code = unique_codes[0]
                litho_by_code = geo_db.lithology.get_lithology_by_code(first_code)
                assert isinstance(litho_by_code, pd.DataFrame)
                if len(litho_by_code) > 0:
                    assert all(litho_by_code["lith_code"] == first_code)

    def test_survey_queries(self, geo_db):
        """Test survey data query methods."""
        # Test getting all survey data
        all_surveys = geo_db.survey.get_all_surveys()
        assert isinstance(all_surveys, pd.DataFrame)

        # Test survey for specific hole
        collar_df = geo_db.collar.get_all_holes()
        if len(collar_df) > 0:
            hole_id = collar_df.iloc[0]["hole_id"]
            hole_survey = geo_db.survey.get_survey_for_hole(hole_id)
            assert isinstance(hole_survey, pd.DataFrame)
            # All survey points should be for the specified hole
            if len(hole_survey) > 0:
                assert all(hole_survey["hole_id"] == hole_id)
