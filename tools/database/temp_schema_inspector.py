import sqlite3
import pandas as pd

def inspect_table_schema(db_path, table_name):
    """Connects to a SQLite DB and prints the schema of a specific table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use PRAGMA to get table info
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema_info = cursor.fetchall()
        
        if not schema_info:
            print(f"Table '{table_name}' not found in {db_path}")
            return
            
        # Format and print the schema
        schema_df = pd.DataFrame(schema_info, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
        print(f"Schema for table '{table_name}' in '{db_path}':")
        print(schema_df)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Hardcoded for our specific use case
    db_file = "data/db/deepseek-chat.db"
    table_to_inspect = "personality"
    inspect_table_schema(db_file, table_to_inspect)
