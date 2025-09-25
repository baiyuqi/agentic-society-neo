import argparse
import sqlite3
import json
import os

def scan_invalid(db_path, expected_length=20, clear_invalid=False):
    """
    Scan a database file for quiz_answer records where agent_answer array length != expected_length.
    Prints sheet_id and persona_id for invalid records.
    Optionally clears agent_answer and response fields for invalid records.

    Args:
        db_path (str): Path to the SQLite database file
        expected_length (int): Expected array length (default: 20)
        clear_invalid (bool): Whether to clear agent_answer and response for invalid records
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return

    # Use read-write mode if clearing invalid records, otherwise read-only
    mode = 'rw' if clear_invalid else 'ro'
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode={mode}', uri=True)
        cursor = conn.cursor()

        # Check if quiz_answer table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_answer'")
        if not cursor.fetchone():
            print(f"Error: quiz_answer table not found in database '{db_path}'")
            conn.close()
            return

        print(f"Scanning database: {db_path}")
        print(f"Looking for records with agent_answer array length != {expected_length}")
        if clear_invalid:
            print("WARNING: Will clear agent_answer and response fields for invalid records!")
        print("-" * 60)

        # Get all records from quiz_answer table
        cursor.execute("SELECT sheet_id, persona_id, agent_answer, response FROM quiz_answer")
        records = cursor.fetchall()

        invalid_count = 0
        total_count = len(records)
        invalid_records = []

        for sheet_id, persona_id, agent_answer_json, response in records:
            # Check for empty string or None first
            if agent_answer_json is None or agent_answer_json.strip() == '':
                print(f"Invalid record - Sheet ID: {sheet_id}, Persona ID: {persona_id}, Empty or None agent_answer")
                invalid_count += 1
                invalid_records.append((sheet_id, persona_id))
                continue

            try:
                # Parse the JSON array
                agent_answer = json.loads(agent_answer_json)

                # Check if it's a list and has the expected length
                if isinstance(agent_answer, list) and len(agent_answer) != expected_length:
                    print(f"Invalid record - Sheet ID: {sheet_id}, Persona ID: {persona_id}, Array length: {len(agent_answer)}")
                    invalid_count += 1
                    invalid_records.append((sheet_id, persona_id))
                elif not isinstance(agent_answer, list):
                    print(f"Invalid format - Sheet ID: {sheet_id}, Persona ID: {persona_id}, Not a list")
                    invalid_count += 1
                    invalid_records.append((sheet_id, persona_id))

            except json.JSONDecodeError as e:
                print(f"JSON decode error - Sheet ID: {sheet_id}, Persona ID: {persona_id}, Error: {e}")
                invalid_count += 1
                invalid_records.append((sheet_id, persona_id))

        # Clear invalid records if requested
        if clear_invalid and invalid_records:
            print("-" * 60)
            print("Clearing agent_answer and response fields for invalid records...")

            cleared_count = 0
            for sheet_id, persona_id in invalid_records:
                try:
                    cursor.execute(
                        "UPDATE quiz_answer SET agent_answer = ?, response = ? WHERE sheet_id = ? AND persona_id = ?",
                        (None, None, sheet_id, persona_id)
                    )
                    cleared_count += 1
                    print(f"Cleared - Sheet ID: {sheet_id}, Persona ID: {persona_id}")
                except Exception as e:
                    print(f"Error clearing record - Sheet ID: {sheet_id}, Persona ID: {persona_id}: {e}")

            conn.commit()
            print(f"Successfully cleared {cleared_count} invalid records")

        conn.close()

        print("-" * 60)
        print(f"Scan completed:")
        print(f"Total records scanned: {total_count}")
        print(f"Invalid records found: {invalid_count}")
        print(f"Valid records: {total_count - invalid_count}")

        if invalid_count == 0:
            print("All records have valid agent_answer arrays")
        else:
            print(f"Warning: Found {invalid_count} invalid records")

    except Exception as e:
        print(f"Error scanning database: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan database for quiz_answer records with invalid agent_answer array length"
    )
    parser.add_argument(
        "db_file",
        help="Path to the SQLite database file to scan"
    )
    parser.add_argument(
        "--expected-length",
        type=int,
        default=20,
        help="Expected array length (default: 20)"
    )
    parser.add_argument(
        "--clear-invalid",
        action="store_true",
        help="Clear agent_answer and response fields for invalid records"
    )

    args = parser.parse_args()

    scan_invalid(args.db_file, args.expected_length, args.clear_invalid)