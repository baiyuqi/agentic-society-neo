import argparse
import pandas as pd
from sqlalchemy import create_engine
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from asociety.repository.database import Base
from asociety.repository.persona_rep import Persona

def infer_workclass(row):
    """
    Infers the workclass from occupation and persona description.
    """
    occupation = row.get('occupation', '').lower()
    # Use the combined description for inference
    description = row.get('combined_persona_desc', '').lower()

    if 'not_in_workforce' in occupation or 'retiree' in occupation:
        return 'Not in workforce'
    
    if any(keyword in description for keyword in ['government', 'federal', 'state', 'local']):
        return 'Government'
        
    if any(keyword in description for keyword in ['self-employed', 'owns his own', 'owns her own', 'freelance', 'entrepreneur']):
        return 'Self-employed'

    return 'Private'

def combine_persona_descriptions(row, persona_columns):
    """
    Combines text from various persona-related columns into a single description.
    """
    description_parts = []
    for col in persona_columns:
        if col in row and pd.notna(row[col]):
            description_parts.append(str(row[col]))
    
    return '\n\n'.join(description_parts)

def convert_and_populate(db_path, samples_table='samples', persona_table='persona'):
    """
    Reads data, combines all persona fields into a single description,
    infers missing data, and inserts it into the persona table.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database '{db_path}' not found.")
        return

    engine = create_engine(f'sqlite:///{db_path}')

    try:
        Base.metadata.create_all(engine, tables=[Persona.__table__])
        df_samples = pd.read_sql_table(samples_table, engine)
        print(f"Read {len(df_samples)} records from '{samples_table}'.")

        # Identify all persona-related columns to combine
        persona_source_cols = [
            'persona', 'professional_persona', 'sports_persona', 'arts_persona', 
            'travel_persona', 'culinary_persona', 'skills_and_expertise', 
            'hobbies_and_interests', 'career_goals_and_ambitions'
        ]
        # Filter to only those that actually exist in the source table
        existing_persona_cols = [col for col in persona_source_cols if col in df_samples.columns]
        print(f"Combining text from columns: {existing_persona_cols}")

        # Transform data
        persona_records = []
        for index, row in df_samples.iterrows():
            # First, create the combined description
            combined_desc = combine_persona_descriptions(row, existing_persona_cols)
            
            # Create a temporary series with the combined description to pass to the inference function
            temp_row_for_inference = row.copy()
            temp_row_for_inference['combined_persona_desc'] = combined_desc

            record = {
                'id': index,
                'sourcePersonaId': row.get('uuid'),
                'age': row.get('age'),
                'sex': row.get('sex'),
                'marital_status': row.get('marital_status'),
                'occupation': row.get('occupation'),
                'native_country': row.get('country'),
                'education': row.get('education_level'),
                'persona_desc': combined_desc,
                'workclass': infer_workclass(temp_row_for_inference),
                'race': None,
                'elicited': None
            }
            persona_records.append(record)
        
        df_to_insert = pd.DataFrame(persona_records)

        print(f"Preparing to insert {len(df_to_insert)} fully combined and populated records...")
        df_to_insert.to_sql(persona_table, engine, if_exists='replace', index=False)
        
        print(f"Successfully inserted {len(df_to_insert)} records into '{persona_table}'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Intelligently convert and populate data from a samples table to the persona table.")
    parser.add_argument('db_path', help='Path to the SQLite database.')
    parser.add_argument('--samples_table', default='samples', help="Name of the source table (default: 'samples').")
    parser.add_argument('--persona_table', default='persona', help="Name of the destination table (default: 'persona').")
    
    args = parser.parse_args()
    convert_and_populate(args.db_path, args.samples_table, args.persona_table)
