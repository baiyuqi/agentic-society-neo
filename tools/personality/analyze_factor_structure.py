import sqlite3
import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo

# --- Mappings derived from asociety/personality/ipipneo ---

# This mapping is based on the algorithmic structure in facet.py
# There are 30 facets, and questions are assigned to them in an interleaved manner.
# Domains are composed of 6 facets each.
DOMAIN_TO_FACETS = {
    "N": [1, 6, 11, 16, 21, 26],
    "E": [2, 7, 12, 17, 22, 27],
    "O": [3, 8, 13, 18, 23, 28],
    "A": [4, 9, 14, 19, 24, 29],
    "C": [5, 10, 15, 20, 25, 30],
}

# From reverse.py
REVERSED_QUESTIONS_120 = [
    9, 19, 24, 30, 39, 40, 48, 49, 51, 53, 54, 60, 62, 67, 68, 69, 70, 73,
    74, 75, 78, 79, 80, 81, 83, 84, 85, 88, 89, 90, 92, 94, 96, 97, 98, 99,
    100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 113, 114,
    115, 116, 118, 119, 120,
]

REVERSED_QUESTIONS_300 = [
    69, 99, 109, 118, 120, 129, 138, 139, 144, 148, 149, 150, 151, 152, 156,
    157, 158, 159, 160, 162, 163, 164, 165, 167, 168, 169, 171, 173, 174,
    175, 176, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189,
    190, 192, 193, 194, 195, 196, 197, 198, 199, 201, 203, 204, 205, 206,
    208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221,
    222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 233, 234, 235, 236,
    238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251,
    253, 252, 254, 255, 256, 257, 259, 258, 260, 261, 262, 263, 264, 265,
    266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279,
    281, 280, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 294,
    293, 295, 296, 297, 298, 299, 300,
]

def get_domain_questions(domain, num_questions=120):
    """Gets all question numbers for a given domain."""
    if num_questions not in [120, 300]:
        raise ValueError("Number of questions must be 120 or 300")
    
    questions_per_facet = 4 if num_questions == 120 else 10
    num_facets = 30
    
    domain_q_numbers = []
    facets = DOMAIN_TO_FACETS[domain]
    for i in range(questions_per_facet):
        for facet_num in facets:
            q_num = i * num_facets + facet_num
            domain_q_numbers.append(q_num)
    return sorted(domain_q_numbers)

def load_data(db_path):
    """Loads and prepares personality data from the database."""
    conn = sqlite3.connect(db_path)
    try:
        df_raw = pd.read_sql_query("SELECT persona_id, personality_json FROM personality", conn)
        if df_raw.empty:
            raise ValueError("The 'personality' table is empty or does not exist.")
            
        all_answers = []
        skipped_count = 0
        for index, row in df_raw.iterrows():
            try:
                if not isinstance(row['personality_json'], str):
                    # print(f"Warning: Skipping persona_id={row['persona_id']} due to non-string JSON content.")
                    skipped_count += 1
                    continue
                
                data = json.loads(row['personality_json'])
                
                # Correctly navigate the nested structure
                answer_list = data.get('person', {}).get('result', {}).get('compare', {}).get('user_answers_original')
                
                if answer_list and isinstance(answer_list, list):
                    answers = {item['id_question']: item['id_select'] for item in answer_list}
                    all_answers.append(answers)
                else:
                    # print(f"Warning: Skipping persona_id={row['persona_id']} due to missing or invalid 'user_answers_original' list.")
                    skipped_count += 1
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                # print(f"Warning: Skipping persona_id={row['persona_id']} due to invalid JSON or structure. Error: {e}")
                skipped_count += 1
        
        if skipped_count > 0:
            print(f"\nSkipped a total of {skipped_count} records due to data errors.\n")

        if not all_answers:
            raise ValueError("No valid answer data could be loaded from the 'personality' table.")

        df = pd.DataFrame(all_answers)
        # Ensure all 120 or 300 columns are present, filling missing with NaN
        num_questions = max(max(d.keys()) for d in all_answers if d)
        if num_questions > 120:
             column_range = range(1, 301)
        else:
             column_range = range(1, 121)
        df = df.reindex(columns=column_range)
        
        # Drop rows with any NaN values, as they can't be used in factor analysis
        df.dropna(inplace=True)
        if len(df) < 2:
            raise ValueError("Not enough valid data rows to perform analysis after dropping NaNs.")

        return df


    finally:
        conn.close()

def analyze_factor_structure_and_visualize(db_path, df):
    """
    Performs Exploratory Factor Analysis (EFA) and visualizes the results.
    """
    num_questions = len(df.columns)
    if num_questions not in [120, 300]:
        print(f"Warning: Found {num_questions} questions. Analysis requires 120 or 300. Skipping.")
        return

    reversed_list = REVERSED_QUESTIONS_120 if num_questions == 120 else REVERSED_QUESTIONS_300
    
    # Reverse score applicable questions
    # Assuming scores are 1-5. Reverse is 6 - score.
    for q_num in reversed_list:
        if q_num in df.columns:
            df[q_num] = 6 - df[q_num]

    # --- Pre-analysis Data Cleaning and Diagnostics ---
    print("--- Pre-analysis Data Cleaning and Diagnostics ---")
    print(f"Initial data shape: {df.shape}")
    
    # Check for NaN values
    if df.isnull().values.any():
        print(f"Found {df.isnull().sum().sum()} NaN values. Dropping rows with NaNs.")
        df.dropna(inplace=True)
        print(f"Shape after dropping NaNs: {df.shape}")

    if df.empty:
        print("Error: DataFrame is empty after dropping NaNs. Cannot proceed.")
        return

    # Check for columns with zero variance
    zero_std_cols = df.columns[df.std() == 0]
    if not zero_std_cols.empty:
        print(f"Found {len(zero_std_cols)} columns with zero standard deviation: {zero_std_cols.tolist()}")
        print("Dropping these columns as they provide no variance.")
        df.drop(columns=zero_std_cols, inplace=True)
        print(f"Shape after dropping zero-variance columns: {df.shape}")

    if df.shape[1] < 5: # Need at least as many variables as factors
        print("Error: Not enough variables left to perform factor analysis. Cannot proceed.")
        return

    print("--- Data Adequacy Check ---")
    # Kaiser-Meyer-Olkin (KMO) Test
    kmo_all, kmo_model = calculate_kmo(df)
    print(f"Kaiser-Meyer-Olkin (KMO) Test: {kmo_model:.3f}")
    if kmo_model < 0.6:
        print("Warning: KMO value is low (< 0.6), indicating data may not be adequate for factor analysis.")

    # Bartlett's Test of Sphericity
    chi_square_value, p_value = calculate_bartlett_sphericity(df)
    print(f"Bartlett's Test of Sphericity: chi-square={chi_square_value:.2f}, p-value={p_value:.3e}")
    if p_value > 0.05:
        print("Warning: Bartlett's test is not significant (p > 0.05), indicating correlations are not large enough for EFA.")
    
    print("\n--- Factor Analysis ---")
    # --- Scree Plot to determine number of factors ---
    fa = FactorAnalyzer(rotation=None, n_factors=len(df.columns))
    fa.fit(df)
    ev, v = fa.get_eigenvalues()
    
    output_prefix = f"factor_analysis_{os.path.splitext(os.path.basename(db_path))[0]}"

    plt.figure(figsize=(10, 6))
    plt.scatter(range(1, df.shape[1] + 1), ev)
    plt.plot(range(1, df.shape[1] + 1), ev)
    plt.title('Scree Plot')
    plt.xlabel('Factors')
    plt.ylabel('Eigenvalue')
    plt.grid()
    scree_plot_path = f"{output_prefix}_scree_plot.png"
    plt.savefig(scree_plot_path)
    print(f"Scree plot saved to: {scree_plot_path}")
    plt.close()

    # --- Perform EFA with 5 factors (based on Big Five theory) ---
    n_factors = 5
    print(f"\nPerforming EFA with {n_factors} factors...")
    fa = FactorAnalyzer(n_factors=n_factors, rotation='varimax')
    fa.fit(df)

    loadings = fa.loadings_
    loadings_df = pd.DataFrame(loadings, index=df.columns, columns=[f'Factor {i+1}' for i in range(n_factors)])
    
    print("Factor Loadings (Top 5 per factor):")
    for i in range(n_factors):
        print(f"\n--- Factor {i+1} ---")
        print(loadings_df[f'Factor {i+1}'].abs().sort_values(ascending=False).head())

    # --- Visualize Factor Loadings with a Heatmap ---
    plt.figure(figsize=(12, 20))
    sns.heatmap(loadings_df, cmap='viridis', annot=False)
    plt.title(f'Factor Loadings (Varimax Rotation)\nSource: {os.path.basename(db_path)}')
    plt.xlabel('Factors')
    plt.ylabel('Question Number')
    plt.tight_layout()
    heatmap_path = f"{output_prefix}_loadings_heatmap.png"
    plt.savefig(heatmap_path)
    print(f"\nFactor loadings heatmap saved to: {heatmap_path}")
    plt.close()

    # --- Save results to database ---
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        analysis_name = f"Factor Analysis (EFA) for {os.path.basename(db_path)}"
        analysis_type = "factor_analysis_efa"
        sample_criteria = json.dumps({
            "source_db": os.path.basename(db_path),
            "sample_size": len(df),
            "dropped_cols": zero_std_cols.tolist()
        })
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_loadings = loadings_df.reset_index().rename(columns={'index': 'question_id'}).to_dict(orient='records')
        
        results = json.dumps({
            "kmo_model": kmo_model,
            "bartlett_chi_square": chi_square_value,
            "bartlett_p_value": p_value,
            "eigenvalues": ev.tolist(),
            "n_factors_extracted": n_factors,
            "factor_loadings": serializable_loadings
        })

        insert_query = """
        INSERT INTO personality_analysis (analysis_name, analysis_type, sample_criteria, results)
        VALUES (?, ?, ?, ?);
        """
        cursor.execute(insert_query, (analysis_name, analysis_type, sample_criteria, results))
        conn.commit()
        print(f"\nSuccessfully saved analysis results to {db_path}")
    except sqlite3.Error as e:
        print(f"\nError saving results to database: {e}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Perform Exploratory Factor Analysis (EFA) on personality quiz data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "db_path",
        type=str,
        help="The full path to the SQLite database file (e.g., 'data/db/deepseek-chat.db')."
    )
    args = parser.parse_args()

    try:
        print(f"--- Starting Factor Analysis for {args.db_path} ---")
        data_df = load_data(args.db_path)
        analyze_factor_structure_and_visualize(args.db_path, data_df)
        print(f"--- Factor Analysis for {args.db_path} Complete ---")
    except (ValueError, sqlite3.Error) as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
