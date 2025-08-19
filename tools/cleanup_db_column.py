import sys
import os
import argparse
from sqlalchemy import create_engine, text, inspect

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from asociety.repository.database import set_currentdb, get_engine, Base

def cleanup_database(db_name):
    """
    Performs cleanup on the specified database:
    1. Drops the 'sourcePersonaId' column from the 'skeleton_persona' table if it exists.
    2. Deletes all records from the 'persona' table.
    """
    db_path = os.path.abspath(os.path.join('data', 'db', db_name))
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}. Nothing to clean.")
        return

    print(f"Starting cleanup for database: {db_path}")
    set_currentdb(db_path)
    engine = get_engine()
    
    with engine.connect() as connection:
        inspector = inspect(engine)
        
        # --- Step 1: Clean up skeleton_persona table ---
        try:
            columns = [col['name'] for col in inspector.get_columns('skeleton_persona')]
            if 'sourcePersonaId' in columns:
                print("Found erroneous 'sourcePersonaId' column in 'skeleton_persona'. Removing it...")
                connection.execute(text('ALTER TABLE skeleton_persona DROP COLUMN sourcePersonaId'))
                print("'sourcePersonaId' column removed.")
            else:
                print("'skeleton_persona' table is already clean (no 'sourcePersonaId' column).")
        except Exception as e:
            print(f"Could not inspect or clean 'skeleton_persona' table. It might not exist yet. Error: {e}")

        # --- Step 2: Clear the persona table ---
        try:
            if 'persona' in inspector.get_table_names():
                print("Clearing all records from the 'persona' table...")
                connection.execute(text('DELETE FROM persona;'))
                print("'persona' table cleared.")
            else:
                print("'persona' table does not exist. No records to clear.")
        except Exception as e:
            print(f"Could not clear 'persona' table. Error: {e}")
        
        # Commit the transaction if using a transactional backend
        if connection.in_transaction():
            connection.commit()

    print("\nDatabase cleanup complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        A one-time utility to clean up the database after a schema error. 
        Removes the 'sourcePersonaId' column from 'skeleton_persona' and clears the 'persona' table.
        """
    )
    parser.add_argument(
        "db_name",
        help="The name of the database file in data/db/ (e.g., 'deepseek-chat-single-5.db')."
    )
    args = parser.parse_args()

    cleanup_database(args.db_name)
