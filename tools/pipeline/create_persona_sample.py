import argparse
import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

# --- Setup Python Path ---
# Add the project root to the Python path to allow importing 'asociety'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from asociety.repository.database import Base
from asociety.repository.persona_rep import Persona
from sqlalchemy import bindparam

# --- Stage 1: Copying Functions (from copy_random_samples.py) ---

def copy_random_samples(source_engine, dest_engine, n, table_name='samples'):
    """
    Copies n random, unique samples from a source to a destination engine's temporary table,
    ensuring they don't already exist in the destination's main samples table.
    The temporary table is replaced on each run.
    """
    temp_table_name = f"temp_{table_name}"
    print(f"\n--- Stage 1: Copying {n} new random samples to temporary table '{temp_table_name}' ---")

    # Get existing UUIDs from the destination's main samples table
    existing_uuids = []
    try:
        with dest_engine.connect() as conn:
            if conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")).scalar_one_or_none():
                result = conn.execute(text(f"SELECT uuid FROM {table_name}")).fetchall()
                existing_uuids = [row[0] for row in result]
                print(f"Found {len(existing_uuids)} existing samples in destination table '{table_name}'.")
    except Exception as e:
        print(f"Warning: Could not read existing UUIDs from '{table_name}'. Assuming none exist. Error: {e}")

    # Check if source table exists
    try:
        with source_engine.connect() as conn:
            if not conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")).scalar_one_or_none():
                print(f"Error: Source table '{table_name}' not found.")
                return None
    except Exception as e:
        print(f"Error checking source DB for table '{table_name}': {e}")
        return None

    # Select n random samples that are not already in the destination
    params = {'n': n}
    if existing_uuids:
        stmt = text(f"SELECT * FROM {table_name} WHERE uuid NOT IN :uuids ORDER BY RANDOM() LIMIT :n")
        stmt = stmt.bindparams(bindparam('uuids', expanding=True))
        params['uuids'] = existing_uuids
    else:
        stmt = text(f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT :n")

    try:
        df = pd.read_sql(stmt, source_engine, params=params)
        
        if len(df) < n:
            print(f"Warning: Could only find {len(df)} new unique samples in the source database (requested {n}).")
            if len(df) == 0:
                print("No new samples to add. Stopping.")
                return None

        # Replace the temporary table on each run
        df.to_sql(temp_table_name, dest_engine, if_exists='replace', index=False)
        print(f"Successfully copied {len(df)} new random samples to '{temp_table_name}'.")
        return temp_table_name
    except Exception as e:
        print(f"Error during copy operation: {e}")
        return None




# --- Stage 2: Appending new samples to the main samples table ---
def append_samples(engine, temp_table_name, main_table_name='samples'):
    """
    Appends records from a temporary table to the main samples table.
    """
    print(f"\n--- Stage 2: Appending '{temp_table_name}' to '{main_table_name}' ---")
    try:
        df_temp = pd.read_sql_table(temp_table_name, engine)
        df_temp.to_sql(main_table_name, engine, if_exists='append', index=False)
        print(f"Successfully appended {len(df_temp)} records to '{main_table_name}'.")
        return True
    except Exception as e:
        print(f"An error occurred while appending to '{main_table_name}': {e}")
        return False

# --- Stage 3: Conversion Functions (from convert_samples_to_personas.py) ---

def infer_workclass(row):
    occupation = row.get('occupation', '').lower()
    description = row.get('combined_persona_desc', '').lower()
    if 'not_in_workforce' in occupation or 'retiree' in occupation: return 'Not in workforce'
    if any(k in description for k in ['government', 'federal', 'state', 'local']): return 'Government'
    if any(k in description for k in ['self-employed', 'owns his own', 'owns her own', 'freelance', 'entrepreneur']): return 'Self-employed'
    return 'Private'

def combine_persona_descriptions(row, persona_columns):
    parts = [str(row[col]) for col in persona_columns if col in row and pd.notna(row[col])]
    return '\n\n'.join(parts)

def convert_and_populate(engine, temp_samples_table, persona_table='persona'):
    """
    Converts data from the temporary samples table to the 'persona' table.
    """
    print(f"\n--- Stage 3: Converting '{temp_samples_table}' to '{persona_table}' ---")
    try:
        Base.metadata.create_all(engine, tables=[Persona.__table__])
        # Read from the temporary table, not the main one
        df_samples = pd.read_sql_table(temp_samples_table, engine)
        
        # Get the last id from the persona table to ensure unique IDs
        last_id = -1
        try:
            with engine.connect() as conn:
                if conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{persona_table}'")).scalar_one_or_none():
                    result = conn.execute(text(f"SELECT MAX(id) FROM {persona_table}")).scalar_one()
                    last_id = result if result is not None else -1
        except Exception as e:
            print(f"Could not read max id from persona table, starting from 0. Error: {e}")
            last_id = -1

        persona_source_cols = [
            'persona', 'professional_persona', 'sports_persona', 'arts_persona', 
            'travel_persona', 'culinary_persona', 'skills_and_expertise', 
            'hobbies_and_interests', 'career_goals_and_ambitions'
        ]
        existing_persona_cols = [col for col in persona_source_cols if col in df_samples.columns]
        print(f"Combining text from columns: {existing_persona_cols}")

        persona_records = []
        for index, row in df_samples.iterrows():
            combined_desc = combine_persona_descriptions(row, existing_persona_cols)
            temp_row = row.copy()
            temp_row['combined_persona_desc'] = combined_desc
            record = {
                'id': last_id + 1 + index, 'sourcePersonaId': row.get('uuid'), 'age': row.get('age'),
                'sex': row.get('sex'), 'marital_status': row.get('marital_status'),
                'occupation': row.get('occupation'), 'native_country': row.get('country'),
                'education': row.get('education_level'), 'persona_desc': combined_desc,
                'workclass': infer_workclass(temp_row), 'race': None, 'elicited': None
            }
            persona_records.append(record)
        
        df_to_insert = pd.DataFrame(persona_records)
        df_to_insert.to_sql(persona_table, engine, if_exists='append', index=False)
        print(f"Successfully inserted {len(df_to_insert)} records into '{persona_table}'.")
        return True
    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        return False

# --- Stage 4: Cleanup ---
def cleanup(engine, table_name):
    print(f"\n--- Stage 4: Cleaning up intermediate tables ---")
    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.commit()
        print(f"Successfully dropped intermediate table '{table_name}'.")
    except Exception as e:
        print(f"Error during cleanup: {e}")


# --- Main Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates a persona sample database by copying and converting records.")
    parser.add_argument('src_db', help='Path to the source SQLite database (e.g., data/db/sampled_6000.db).')
    parser.add_argument('dst_db', help='Path to the destination SQLite database to create (e.g., data/db/test.db).')
    parser.add_argument('-n', type=int, required=True, help='Number of random samples to process.')
    parser.add_argument('--samples_table', default='samples', help="Name of the source and main samples table.")
    parser.add_argument('--persona_table', default='persona', help="Name of the final persona table.")
    parser.add_argument('--keep-temp-samples', action='store_true', help="If set, does not delete the intermediate temporary samples table.")
    
    args = parser.parse_args()

    if not os.path.exists(args.src_db):
        print(f"Error: Source database '{args.src_db}' not found.")
        sys.exit(1)

    source_engine = create_engine(f'sqlite:///{args.src_db}')
    dest_engine = create_engine(f'sqlite:///{args.dst_db}')

    print(f"Starting persona sample creation pipeline...")
    print(f"Source: {args.src_db}\nDestination: {args.dst_db}\nNumber of samples: {args.n}")

    temp_table = copy_random_samples(source_engine, dest_engine, args.n, args.samples_table)
    if temp_table:
        if append_samples(dest_engine, temp_table, args.samples_table):
            if convert_and_populate(dest_engine, temp_table, args.persona_table):
                if not args.keep_temp_samples:
                    cleanup(dest_engine, temp_table)
                else:
                    print("\n--- Stage 4: Skipping cleanup as requested ---")
                    print(f"Intermediate table '{temp_table}' was kept in '{args.dst_db}'.")
                print("\nPipeline completed successfully!")
            else:
                print("\nPipeline failed during conversion stage.")
                sys.exit(1)
        else:
            print("\nPipeline failed during append stage.")
            sys.exit(1)
    else:
        print("\nPipeline failed during copy stage.")
        sys.exit(1)
