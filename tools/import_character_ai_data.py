import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from tqdm import tqdm

# --- Configuration ---
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'character.db')
JSON_SOURCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'character-ai-open-v2.0.json')
LLM_MODEL = "deepseek"
MAX_WORKERS = 15
TARGET_TOTAL_RECORDS = 600 # Stop when the table has this many records in total

# --- LLM Initialization ---
def get_llm_engine(model_name: str):
    """Initializes and returns a specific LLM engine."""
    if model_name == 'deepseek':
        apikey = os.getenv('DS_API_KEY')
        api_base = os.getenv('DS_BASE_URL')
        if not apikey or not api_base:
            raise ValueError("DS_API_KEY or DS_BASE_URL environment variable not set.")
        return ChatOpenAI(model="deepseek-chat", openai_api_base=api_base, api_key=apikey)
    else:
        raise ValueError(f"Unsupported model for this tool: {model_name}")

# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def get_max_processed_id(conn):
    """Finds the maximum ID currently in the persona table."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM persona")
    result = cursor.fetchone()[0]
    return result if result is not None else 0

def get_current_record_count(conn):
    """Counts the total number of rows in the persona table."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM persona")
    result = cursor.fetchone()[0]
    return result if result is not None else 0

def insert_persona(conn, persona_id: int, persona_data: dict):
    """Inserts a single persona record into the database with a specific ID."""
    sql = ''' INSERT INTO persona(id, age, workclass, education, marital_status, occupation, race, sex, native_country, persona_desc, sourcePersonaId)
              VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
    
    params = (
        persona_id,
        persona_data.get('age'),
        persona_data.get('workclass'),
        persona_data.get('education'),
        persona_data.get('marital_status'),
        persona_data.get('occupation'),
        persona_data.get('race'),
        persona_data.get('sex'),
        persona_data.get('native_country'),
        persona_data.get('persona_desc'),
        f"{persona_id}@{persona_data.get('name', 'unknown')}@character-ai"
    )
    
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()

# --- LLM Processing ---
def get_extraction_prompt(description: str) -> str:
    """Formats the prompt for the LLM."""
    return f"""
You are an expert data extraction assistant. Your task is to carefully read the provided character description and extract the specified information.
Return the information as a single, valid JSON object. Do not add any explanations or text outside of the JSON object.

The JSON object must have the following keys: "name", "age", "workclass", "education", "marital_status", "occupation", "race", "sex", "native_country", and "persona_desc".

**CRITICAL INSTRUCTIONS FOR the "age" field:**
- You MUST provide an integer value for "age".
- If an explicit age is mentioned, use that number.
- If no explicit age is given, you MUST estimate a reasonable integer age based on the context. For example:
  - "high school student" or "高中生" -> estimate 17
  - "university student" or "大学生" -> estimate 20
  - "young man" or "青年" -> estimate 25
  - "veteran" or "经验丰富" -> estimate 45
- Only if it is absolutely impossible to estimate an age from the context should you return null. Prioritize estimation.

- "name": The character's name (e.g., "雪之下雪乃").
- "sex": "Male" or "Female".
- "persona_desc": The original, full character description text provided in the input.
- For all other fields ("workclass", "education", "marital_status", "occupation", "race", "native_country"), extract the information if it is present. If the information is not mentioned in the text, the value must be null.

Here is the character description:
---
{description}
---
"""

def process_character(character_json: dict, llm: ChatOpenAI):
    """
    Processes a single character entry: sends to LLM, parses response.
    """
    instruction = character_json.get("instruction", "")
    dialogue = character_json.get("output", "")

    if not instruction:
        return None

    # Combine instruction and dialogue for a richer context
    full_description = f"{instruction}\n\n--- Example Dialogue ---\n\n{dialogue}"

    prompt = get_extraction_prompt(full_description)
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        cleaned_response = response.content.strip().replace('```json', '').replace('```', '')
        extracted_data = json.loads(cleaned_response)
        return extracted_data
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse JSON from LLM response: {response.content}")
        return None
    except Exception as e:
        print(f"An error occurred during LLM invocation: {e}")
        return None

# --- Main Execution ---
def main():
    print("Starting Character.AI data import process...")
    
    conn = get_db_connection()
    
    # 1. Check current and target record counts
    current_count = get_current_record_count(conn)
    print(f"Database currently contains {current_count} records.")
    
    if current_count >= TARGET_TOTAL_RECORDS:
        print(f"Target of {TARGET_TOTAL_RECORDS} records already met or exceeded. Exiting.")
        conn.close()
        return
        
    records_to_import = TARGET_TOTAL_RECORDS - current_count
    print(f"Target is {TARGET_TOTAL_RECORDS} records. Need to import {records_to_import} more.")

    # 2. Get max ID to know where to start reading from the source file
    max_id = get_max_processed_id(conn)
    
    # 3. Read and filter source data
    try:
        with open(JSON_SOURCE_PATH, 'r', encoding='utf-8') as f:
            all_source_data = [json.loads(line) for line in f]
        
        unprocessed_data = [(i + 1, record) for i, record in enumerate(all_source_data) if i + 1 > max_id]
        
        if not unprocessed_data:
            print("No new data to process. Exiting.")
            conn.close()
            return
            
    except FileNotFoundError:
        print(f"Error: Source file not found at {JSON_SOURCE_PATH}")
        conn.close()
        return
    except Exception as e:
        print(f"Error reading or filtering source file: {e}")
        conn.close()
        return

    # 4. Initialize LLM
    try:
        llm = get_llm_engine(LLM_MODEL)
        print(f"LLM Engine '{LLM_MODEL}' initialized.")
    except ValueError as e:
        print(f"Error: {e}")
        conn.close()
        return

    # 5. Process and insert data
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_id = {executor.submit(process_character, char_data, llm): char_id for char_id, char_data in unprocessed_data}
        
        successful_imports = 0
        failed_imports = 0
        
        with tqdm(total=records_to_import, desc="Importing to reach target") as pbar:
            for future in as_completed(future_to_id):
                if successful_imports >= records_to_import:
                    print(f"\nTarget of {records_to_import} new records reached. Stopping...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                persona_id = future_to_id[future]
                try:
                    extracted_data = future.result()
                    if extracted_data and extracted_data.get('age') is not None:
                        insert_persona(conn, persona_id, extracted_data)
                        successful_imports += 1
                        pbar.update(1)
                    else:
                        failed_imports += 1
                except Exception as e:
                    print(f"An error occurred while inserting data for ID {persona_id}: {e}")
                    failed_imports += 1
                
                pbar.set_postfix_str(f"Success: {successful_imports}, Failed: {failed_imports}")

    conn.close()
    print("\nProcess finished.")
    print(f"Successfully imported {successful_imports} new personas.")
    print(f"Failed to import {failed_imports} new personas.")

if __name__ == "__main__":
    main()