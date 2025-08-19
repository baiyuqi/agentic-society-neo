import argparse
import pandas as pd
from sqlalchemy import create_engine, text
import os

def copy_random_samples(source_db, dest_db, n, table_name='sample'):
    """
    Copies n random, unique samples from a table in a source SQLite database to a destination SQLite database.
    """
    if not os.path.exists(source_db):
        print(f"Error: Source database '{source_db}' not found.")
        return

    print(f"Connecting to source DB: {source_db}")
    source_engine = create_engine(f'sqlite:///{source_db}')

    print(f"Connecting to destination DB: {dest_db}")
    dest_engine = create_engine(f'sqlite:///{dest_db}')

    # Get table schema from source
    try:
        with source_engine.connect() as conn:
            table_names_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            table_names = [name[0] for name in table_names_result]
            
            if table_name not in table_names:
                print(f"Error: Table '{table_name}' not found in source database '{source_db}'.")
                print(f"Available tables are: {table_names}")
                return

            create_table_sql_result = conn.execute(text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")).scalar_one_or_none()
            if not create_table_sql_result:
                # This case should theoretically not be reached if the above check passes
                print(f"Error: Could not retrieve schema for table '{table_name}'.")
                return
            create_table_sql = create_table_sql_result
    except Exception as e:
        print(f"Error reading schema from source DB: {e}")
        return

    # Create table in destination if it doesn't exist
    with dest_engine.connect() as conn:
        # Ensure the table is created with the same schema
        create_if_not_exists_sql = create_table_sql.replace(f'CREATE TABLE {table_name}', f'CREATE TABLE IF NOT EXISTS {table_name}')
        conn.execute(text(create_if_not_exists_sql))
        conn.commit()
        print(f"Ensured table '{table_name}' exists in destination DB '{dest_db}'.")


    # Select n random samples
    print(f"Selecting {n} random samples from '{table_name}'...")
    query = f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT {n}"
    
    try:
        df = pd.read_sql(query, source_engine)
    except Exception as e:
        print(f"Error reading data from source table: {e}")
        return

    if len(df) < n:
        print(f"Warning: Source table has fewer than {n} records. Copied {len(df)} records.")

    # Write to destination, replacing existing data in the destination table
    print(f"Writing {len(df)} samples to destination table...")
    try:
        # Clear the table before inserting new data to ensure only the new random sample exists
        with dest_engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()
        
        df.to_sql(table_name, dest_engine, if_exists='append', index=False)
        print(f"Successfully copied {len(df)} random samples from '{source_db}' to '{dest_db}'.")
    except Exception as e:
        print(f"Error writing data to destination table: {e}")


def verify_db(db_path, n, table_name='sample'):
    if not os.path.exists(db_path):
        print(f"Verification failed: Database '{db_path}' not found.")
        return
    
    engine = create_engine(f'sqlite:///{db_path}')
    try:
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()
            if count == n:
                print(f"Verification successful: Found {count} records in '{table_name}' table in '{db_path}'.")
            else:
                print(f"Verification failed: Expected {n} records, but found {count} in '{table_name}' table in '{db_path}'.")
    except Exception as e:
        print(f"An error occurred during verification: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy n random samples from one SQLite DB to another, or verify the contents of a DB.')
    
    # Verification arguments
    parser.add_argument('--verify', action='store_true', help='Verify the number of records in the destination DB.')
    parser.add_argument('--db_path', help='Path to the database for verification.')
    
    # Copy arguments
    parser.add_argument('--source_db', help='Path to the source SQLite database.')
    parser.add_argument('--dest_db', help='Path to the destination SQLite database.')
    
    # Common arguments
    parser.add_argument('-n', type=int, help='Number of samples.')
    parser.add_argument('--table_name', default='sample', help='Name of the table (default: sample).')

    args = parser.parse_args()

    if args.verify:
        if args.db_path and args.n is not None:
            verify_db(args.db_path, args.n, args.table_name)
        else:
            print("Error: For verification, --db_path and -n arguments are required.")
            parser.print_help()
    elif args.source_db and args.dest_db and args.n is not None:
        copy_random_samples(args.source_db, args.dest_db, args.n, args.table_name)
    else:
        print("Error: For copying, --source_db, --dest_db, and -n are required.")
        parser.print_help()
