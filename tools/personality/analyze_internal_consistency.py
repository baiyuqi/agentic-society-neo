import sqlite3
import argparse
import json
import pandas as pd
import pingouin as pg
import matplotlib.pyplot as plt
import os

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
                    print(f"Warning: Skipping persona_id={row['persona_id']} due to non-string JSON content.")
                    skipped_count += 1
                    continue
                
                data = json.loads(row['personality_json'])
                
                # Correctly navigate the nested structure
                answer_list = data.get('person', {}).get('result', {}).get('compare', {}).get('user_answers_original')
                
                if answer_list and isinstance(answer_list, list):
                    answers = {item['id_question']: item['id_select'] for item in answer_list}
                    all_answers.append(answers)
                else:
                    print(f"Warning: Skipping persona_id={row['persona_id']} due to missing or invalid 'user_answers_original' list.")
                    skipped_count += 1
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                print(f"Warning: Skipping persona_id={row['persona_id']} due to invalid JSON or structure. Error: {e}")
                skipped_count += 1
        
        if skipped_count > 0:
            print(f"\nSkipped a total of {skipped_count} records due to data errors.\n")

        if not all_answers:
            raise ValueError("No valid answer data could be loaded from the 'personality' table.")

        df = pd.DataFrame(all_answers)
        # Ensure all 120 or 300 columns are present, filling missing with NaN
        num_questions = max(max(d.keys()) for d in all_answers)
        if num_questions > 120:
             column_range = range(1, 301)
        else:
             column_range = range(1, 121)
        df = df.reindex(columns=column_range)
        return df


    finally:
        conn.close()

def analyze_and_save(db_path, df):
    """Calculates Cronbach's alpha, saves results to DB, and creates a plot."""
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

    # Calculate Cronbach's alpha for each domain
    alphas = {}
    domains = ["O", "C", "E", "A", "N"]
    for domain in domains:
        domain_questions = get_domain_questions(domain, num_questions)
        # Ensure we only select columns that actually exist in the dataframe
        existing_domain_questions = [q for q in domain_questions if q in df.columns]
        
        if not existing_domain_questions:
            print(f"Warning: No questions found for domain '{domain}'. Skipping.")
            continue

        domain_df = df[existing_domain_questions]
        alpha_results = pg.cronbach_alpha(data=domain_df)
        alphas[domain] = alpha_results[0]
        print(f"Domain: {domain}, Cronbach's Alpha: {alpha_results[0]:.3f}")

    # --- Save results to database ---
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        analysis_name = f"Internal Consistency for {os.path.basename(db_path)}"
        analysis_type = "internal_consistency"
        sample_criteria = json.dumps({"source_db": os.path.basename(db_path), "sample_size": len(df)})
        results = json.dumps({"cronbach_alpha": alphas})

        insert_query = """
        INSERT INTO personality_analysis (analysis_name, analysis_type, sample_criteria, results)
        VALUES (?, ?, ?, ?);
        """
        cursor.execute(insert_query, (analysis_name, analysis_type, sample_criteria, results))
        conn.commit()
        print(f"\nSuccessfully saved analysis results to {db_path}")
    finally:
        conn.close()

    # --- Create and save visualization ---
    output_filename = f"internal_consistency_{os.path.splitext(os.path.basename(db_path))[0]}.png"
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots()
    
    domain_names = {"O": "Openness", "C": "Conscientiousness", "E": "Extraversion", "A": "Agreeableness", "N": "Neuroticism"}
    bars = ax.bar(domain_names.values(), alphas.values(), color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])

    ax.set_ylabel("Cronbach's Alpha (α)")
    ax.set_title(f"Internal Consistency Reliability\n(Source: {os.path.basename(db_path)})")
    ax.set_ylim(0, 1)
    ax.axhline(y=0.7, color='grey', linestyle='--', linewidth=1)
    ax.text(len(domains)-0.5, 0.71, 'Acceptable (0.7)', color='grey', ha='center')

    # Add alpha values on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.3f}', ha='center', va='bottom')

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"Successfully created visualization: {output_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate and visualize the internal consistency (Cronbach's Alpha) for a given dataset.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "db_path",
        type=str,
        help="The full path to the SQLite database file (e.g., 'data/db/deepseek-chat.db')."
    )
    args = parser.parse_args()

    try:
        print(f"--- Starting Analysis for {args.db_path} ---")
        data_df = load_data(args.db_path)
        analyze_and_save(args.db_path, data_df)
        print(f"--- Analysis for {args.db_path} Complete ---")
    except (ValueError, sqlite3.Error) as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
