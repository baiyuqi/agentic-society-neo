#!/usr/bin/env python3
"""
Duplicate the single persona record 299 times to create 300 identical records.
"""

import sqlite3

def duplicate_persona_records(db_path):
    """Duplicate the single persona record 299 times."""
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the current record
    cursor.execute("SELECT * FROM persona")
    original_record = cursor.fetchone()
    
    if not original_record:
        print("No records found in persona table")
        return
    
    print(f"Original record ID: {original_record[0]}")
    
    # Get column names (excluding id since it's auto-increment)
    cursor.execute("PRAGMA table_info(persona)")
    columns_info = cursor.fetchall()
    # Get column names without the id column
    data_columns = [col[1] for col in columns_info if col[1] != 'id']
    print(f"Data columns: {data_columns}")
    
    # Get the data values (excluding id)
    data_values = original_record[1:]  # Skip the id
    
    # Create INSERT statement without specifying id
    placeholders = ', '.join(['?'] * len(data_values))
    insert_sql = f"INSERT INTO persona ({', '.join(data_columns)}) VALUES ({placeholders})"
    
    # Create 299 duplicate records
    for i in range(299):
        cursor.execute(insert_sql, data_values)
    
    # Commit changes
    conn.commit()
    
    # Verify count
    cursor.execute("SELECT COUNT(*) FROM persona")
    count = cursor.fetchone()[0]
    print(f"Total records after duplication: {count}")
    
    conn.close()
    print("Duplication completed successfully!")

if __name__ == "__main__":
    # Process only the second database (first one already has duplicates)
    db_path = "data/db/deepseek-single-300-narrative-2.db"
    print(f"\nProcessing {db_path}:")
    duplicate_persona_records(db_path)