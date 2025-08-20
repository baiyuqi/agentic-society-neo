
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
import json
import os

from asociety.personality.ipipneo import IpipNeo

# --- Database Setup ---
DB_PATH = 'data/db/human.db'


def setup_database():
 
    engine = create_engine(f'sqlite:///{DB_PATH}')
   
    return engine

# --- Data Parsing ---
def parse_dat_file(file_path, nrows=None):
    """Parses the IPIP120.dat file."""
    def fwf_range(start, end):
        return (start - 1, end)

    colspecs = [
        fwf_range(1, 6),    # CASE
        fwf_range(7, 7),    # SEX
        fwf_range(8, 9),    # AGE
    ] + [fwf_range(32 + i, 32 + i) for i in range(120)]

    column_names = ["CASE", "SEX", "AGE"] + [f"I{i+1}" for i in range(120)]

    df = pd.read_fwf(
        file_path,
        colspecs=colspecs,
        names=column_names,
        dtype=str,
        nrows=nrows
    )

    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    #df.to_csv('d:/output2.csv', index=False, encoding='utf-8')  
    
    # Convert types, handling errors
    df["SEX"] = df["SEX"].replace({'1': 'M', '2': 'F'}).astype(str)
    df["AGE"] = pd.to_numeric(df["AGE"], errors='coerce')
    
    item_cols = [f"I{i+1}" for i in range(120)]
    df[item_cols] = df[item_cols].apply(pd.to_numeric, errors='coerce')
    df[item_cols] = df[item_cols].replace(0, pd.NA)
    
    # Drop rows with invalid age or all answers missing
    df.dropna(subset=['AGE'], inplace=True)
    # The IpipNeo class requires all 120 answers. Drop rows that don't have them all.
    df.dropna(subset=item_cols, how='any', inplace=True)
    
    df["AGE"] = df["AGE"].astype(int)
    df["CASE"] = df["CASE"].astype(int)

    return df

# --- Personality Calculation & Insertion ---
def calculate_and_insert(df, session):
    for _, row in df.iterrows():
        answers = []
        for i in range(120):
            q_id = i + 1
            answer_val = row[f"I{q_id}"]
            if pd.notna(answer_val):
                answers.append({"id_question": q_id, "id_select": int(answer_val), "reverse_scored": 0})

        if len(answers) != 120:
            continue

        try:
            # Keep existing personality object creation
            from asociety.personality.personality_extractor import personality_by
            p = personality_by(row['CASE'], row['SEX'], row['AGE'], answers)
            
            # Direct insertion for persona table
            persona_id = row['CASE']
            sex_str = 'Male' if row['SEX'] == 'M' else 'Female'
            
            persona_insert_stmt = sqlalchemy.text(
                "INSERT INTO persona (id, age, sex) VALUES (:id, :age, :sex)"
            )
            session.execute(persona_insert_stmt, {'id': persona_id, 'age': row['AGE'], 'sex': sex_str})

            # Add the personality object to the session
            session.add(p)
        except Exception as e:
            print(f"Could not process row {row['CASE']}: {e}")
    
    session.commit()

def main():
    """Main function to run the tool."""
    dat_file = '.././IPIP120.dat'
    if not os.path.exists(dat_file):
        print(f"Error: Data file not found at {dat_file}")
        return

    print("Setting up database...")
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"Parsing data from {dat_file}...")
    # For demonstration, let's process the first 100 rows
    data_df = parse_dat_file(dat_file, nrows=10000) 
    
    print(f"Found {len(data_df)} valid rows to process.")
    
    print("Calculating personalities and inserting into database...")
    calculate_and_insert(data_df, session)
    
    print(f"Processing complete. Data inserted into {DB_PATH}")
    session.close()

if __name__ == "__main__":
    main()
