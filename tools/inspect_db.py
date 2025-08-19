import sqlite3
import pandas as pd
import argparse
import os

def inspect_db(db_path, table_name):
    """Prints the schema and a few rows from the specified table in the database."""
    try:
        with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as conn:
            print(f"--- Inspecting table: '{table_name}' in '{db_path}' ---")
            
            # Check if table exists
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if cursor.fetchone() is None:
                print(f"Table '{table_name}' does not exist.")
                print("="*50 + "\n")
                return

            # Print schema
            print(f"Schema:")
            schema = pd.read_sql_query(f"PRAGMA table_info({table_name});", conn)
            print(schema)
            
            # Print a few rows
            print(f"\nSample data (first 5 rows):")
            data = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", conn)
            print(data)
            print("="*50 + "\n")

    except Exception as e:
        print(f"An error occurred while inspecting '{db_path}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspects the schema and content of tables in a SQLite database."
    )
    parser.add_argument(
        "db_file",
        help="The absolute path to the SQLite database file to inspect."
    )
    args = parser.parse_args()

    if not os.path.isabs(args.db_file):
        print(f"Error: Please provide an absolute path to the database file.")
    else:
        inspect_db(args.db_file, 'persona')
        inspect_db(args.db_file, 'skeleton_persona')
