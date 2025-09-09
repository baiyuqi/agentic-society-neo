
import pandas as pd
import sqlite3
import os

# --- Configuration ---
# It's better to use relative paths to make the script more portable
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, 'data', 'db')

input_parquet_path = os.path.join(data_dir, 'train-00000-of-00001.parquet')
output_db_path = os.path.join(data_dir, 'sampled_60000.db')
table_name = 'samples'
num_samples = 6000

# --- Logic ---
print(f"Reading data from {input_parquet_path}...")
try:
    df = pd.read_parquet(input_parquet_path)
    print(f"Successfully loaded {len(df)} rows.")

    if len(df) < num_samples:
        print(f"Warning: The input file has only {len(df)} rows, which is less than the requested {num_samples} samples. Using all rows instead.")
        sample_df = df
    else:
        print(f"Sampling {num_samples} rows randomly (without replacement)...")
        # Use a fixed random_state for reproducibility
        sample_df = df.sample(n=num_samples, replace=False, random_state=42)
        print("Sampling complete.")

    print(f"Writing sampled data to SQLite database at {output_db_path} in table '{table_name}'...")
    conn = sqlite3.connect(output_db_path)
    # Use if_exists='replace' to ensure the script is idempotent
    # Use index=False as the DataFrame index is not needed in the SQL table
    sample_df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

    print(f"Done. The sampled data has been saved to {output_db_path}")

except FileNotFoundError:
    print(f"Error: Input file not found at {input_parquet_path}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

