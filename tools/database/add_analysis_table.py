import sqlite3
import argparse
import datetime
import json

def create_personality_analysis_table(db_path):
    """
    Connects to a SQLite database and creates the 'personality_analysis' table if it doesn't exist.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Use "CREATE TABLE IF NOT EXISTS" to make the script idempotent
        create_table_query = """
        CREATE TABLE IF NOT EXISTS personality_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_name TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            sample_criteria TEXT,
            results TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        # Note: SQLite doesn't have a dedicated JSON type, so we use TEXT and store JSON strings.
        
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Successfully ensured 'personality_analysis' table exists in {db_path}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add the 'personality_analysis' table to a specified agentic society database.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "db_path",
        type=str,
        help="The full path to the SQLite database file (e.g., 'data/db/deepseek-chat.db')."
    )

    args = parser.parse_args()
    create_personality_analysis_table(args.db_path)
