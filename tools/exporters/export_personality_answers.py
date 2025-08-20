# D:/mcp-space/agentic-society/tools/export_personality_answers.py

import sqlite3
import json
import csv
import argparse
import sys

def export_answers_to_csv(db_path, csv_path):
    """
    Connects to a SQLite database, reads the personality table,
    parses the personality_json field, and writes the answers to a CSV file.

    Args:
        db_path (str): The path to the SQLite database file.
        csv_path (str): The path to the output CSV file.
    """
    print(f"Connecting to database: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Fetch persona_id and the JSON data from the personality table
            try:
                cursor.execute("SELECT persona_id, personality_json FROM personality")
                rows = cursor.fetchall()
            except sqlite3.OperationalError as e:
                print(f"Error querying the database: {e}", file=sys.stderr)
                print("Please ensure the 'personality' table and 'persona_id', 'personality_json' columns exist.", file=sys.stderr)
                return

            if not rows:
                print("No data found in the personality table.")
                return

            print(f"Found {len(rows)} records. Preparing to write to {csv_path}...")

            # Prepare the CSV file
            header = ['persona_id'] + [f'I{i}' for i in range(1, 121)]
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)

                for persona_id, json_data_string in rows:
                    if not json_data_string:
                        print(f"Warning: Skipping persona_id {persona_id} due to empty personality_json.", file=sys.stderr)
                        continue
                    
                    try:
                        data = json.loads(json_data_string)
                    except json.JSONDecodeError:
                        print(f"Warning: Skipping persona_id {persona_id} due to invalid JSON.", file=sys.stderr)
                        continue

                    # Navigate through the nested JSON to find the answers
                    # The structure is based on the ipipneo library's output
                    try:
                        reversed_answers = data['person']['result']['compare']['user_answers_reversed']
                    except KeyError:
                        print(f"Warning: Skipping persona_id {persona_id}. Could not find 'user_answers_reversed' in the expected JSON path.", file=sys.stderr)
                        continue

                    # The answers are not guaranteed to be in order.
                    # We must build the answer list based on 'id_question'.
                    answers = [None] * 120
                    for answer_item in reversed_answers:
                        q_id = answer_item.get('id_question')
                        selection = answer_item.get('id_select')
                        
                        if q_id and isinstance(q_id, int) and 1 <= q_id <= 120:
                            answers[q_id - 1] = selection
                    
                    # Write the persona_id followed by all 120 answers
                    writer.writerow([persona_id] + answers)

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        return
    except IOError as e:
        print(f"File error: {e}", file=sys.stderr)
        return

    print(f"\nSuccessfully exported data to {csv_path}")

def main():
    """
    Main function to parse command-line arguments and run the export tool.
    """
    parser = argparse.ArgumentParser(
        description="Export IPIP-NEO personality answers from a database to a CSV file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "db_path",
        help="Path to the input SQLite database file."
    )
    parser.add_argument(
        "csv_path",
        help="Path for the output CSV file."
    )
    
    args = parser.parse_args()
    export_answers_to_csv(args.db_path, args.csv_path)

if __name__ == '__main__':
    main()
