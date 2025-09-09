import argparse
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from asociety.generator.persona_generator import PersonaGeneratorFactory
from asociety.generator.persona_skeleton_generator import PersonaSkeletonGeneratorFactory as SkeletonFactory
from asociety.repository.database import create_tables

def main():
    """
    Main function to run the two-step persona generation process.
    Step 1: Generate and save new skeletons.
    Step 2: Find all unprocessed skeletons in the DB, enrich them, and save to the persona table.
    """
    # Ensure the database and tables exist before doing anything
    print("Initializing database and creating tables if they don't exist...")
    create_tables()
    print("Database is ready.")

    parser = argparse.ArgumentParser(
        description="""
        Runs the persona generation pipeline. First, it generates and saves a specified number of new skeletons.
        Second, it scans the database for ALL skeletons that have not yet been processed and enriches them.
        """
    )
    parser.add_argument(
        "count",
        type=int,
        nargs='?',
        default=1,
        help="Number of new skeletons to generate and save. If 0, only the enrichment step is run."
    )
    args = parser.parse_args()

    # --- Step 1: Generate and Save Skeletons ---
    if args.count > 0:
        print(f"--- Step 1: Generating and saving {args.count} new skeletons ---")
        skeleton_generator = SkeletonFactory.create()
        skeleton_generator.sampling(args.count) # This method now saves directly
    else:
        print("--- Step 1: Skipped (count is 0) ---")

    # --- Step 2: Enrich All Unprocessed Skeletons ---
    print("\n--- Step 2: Enriching all unprocessed skeletons in the database ---")
    enricher = PersonaGeneratorFactory.create()
    enricher.enrich_unprocessed_skeletons()
    print("Enrichment process complete.")

if __name__ == "__main__":
    main()
