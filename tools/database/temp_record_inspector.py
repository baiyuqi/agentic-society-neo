import sqlite3
import json

def inspect_first_record(db_path, table_name):
    """Connects to a SQLite DB and prints the first JSON record from a table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT personality_json FROM {table_name} LIMIT 1;")
        record = cursor.fetchone()
        
        if not record:
            print(f"Table '{table_name}' is empty.")
            return
            
        print(f"Inspecting the first 'personality_json' record from '{db_path}':")
        # Pretty-print the JSON
        parsed_json = json.loads(record[0])
        print(json.dumps(parsed_json, indent=2))

    except (sqlite3.Error, json.JSONDecodeError, TypeError) as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_file = "data/db/deepseek-chat.db"
    table_to_inspect = "personality"
    inspect_first_record(db_file, table_to_inspect)
