"""
Example usage of the pyaccess library.
"""

from pathlib import Path

from pyaccess import GeologicalDatabase


def main():
    """Demonstrate pyaccess library usage."""
    # Path to the Access database
    db_path = Path(__file__).parent.parent / "resources" / "ilbb_all.accdb"

    try:
        # Open the geological database
        with GeologicalDatabase(db_path) as db:
            print("Successfully connected to database!")
            print(f"Available tables: {db.get_tables()}")

            # Get collar data for all holes
            collar_data = db.collar.get_all_holes()
            print(f"\nFound {len(collar_data)} drill holes")

            if len(collar_data) > 0:
                print("\nFirst few holes:")
                print(collar_data.head())

                # Get data for a specific hole (if it exists)
                first_hole_id = collar_data.iloc[0]["hole_id"]
                print(f"\nData for hole {first_hole_id}:")

                hole_data = db.get_complete_hole_data(first_hole_id)
                print(f"Collar data: {hole_data['collar'] is not None}")
                print(f"Survey points: {len(hole_data['survey'])}")
                print(f"Lithology intervals: {len(hole_data['lithology'])}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
