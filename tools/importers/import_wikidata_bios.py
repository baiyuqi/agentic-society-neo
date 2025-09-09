import argparse
import sqlite3
import requests
import wikipediaapi
from tqdm import tqdm
import time
import os
import random
from datetime import datetime

# --- Configuration ---
DB_DIRECTORY = "data/db"
DB_PATH = os.path.join(DB_DIRECTORY, "wiki-fiction.db")
TABLE_NAME = "persona"
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "AgenticSociety/1.0 (https://github.com/ByteDance/agentic-society; contact@example.com)"
REQUEST_TIMEOUT = 180
BATCH_SIZE = 20  # Hardcoded as per user request.
START_YEAR = 1940 # Hardcoded as per user request.


def calculate_age(birth_date_str, death_date_str):
    """
    Calculates age from ISO date strings with a definitive, simplified, and robust logic.
    """
    if not birth_date_str:
        return None
    try:
        birth_year = int(birth_date_str.split('-')[0])
        end_year = datetime.now().year
        age = end_year - birth_year
        if age < 0 or age > 130:
            return None
        return age
    except (ValueError, TypeError, IndexError):
        return None

def get_person_ids_for_year(year, limit=2, offset=0):
    """
    Fetches a paginated batch of people born in a specific, given year using LIMIT and OFFSET.
    """
    query = f"""
    SELECT ?item ?article WHERE {{
      ?item wdt:P31 wd:Q15632617.
      ?item wdt:P21 ?sex_node.
      ?item wdt:P569 ?birthDate.
      FILTER(YEAR(?birthDate) = {year})
      FILTER NOT EXISTS {{ ?item wdt:P570 ?deathDate. }}
      ?article schema:about ?item;
               schema:inLanguage \"en\";
               schema:isPartOf <https://en.wikipedia.org/>.
    }}
    LIMIT {limit}
    OFFSET {offset}
    """
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    try:
        response = requests.get(WIKIDATA_SPARQL_URL, headers=headers, params={'query': query, 'format': 'json'}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        bindings = response.json()['results']['bindings']
        return [{'id': item['item']['value'].split('/')[-1], 'title': item['article']['value'].split('/')[-1]} for item in bindings]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for year {year} with offset {offset}: {e}")
        return []

def get_person_details(person_id):
    """Step 2: Gets structured details for a single person ID using a more robust, explicit query."""
    query = f"""
    SELECT
      (GROUP_CONCAT(DISTINCT ?sex_label; separator=", ") AS ?sex)
      (SAMPLE(?birthDate) AS ?dob)
      (SAMPLE(?deathDate) AS ?dod)
      (GROUP_CONCAT(DISTINCT ?occupation_label; separator=", ") AS ?occupations)
      (GROUP_CONCAT(DISTINCT ?country_label; separator=", ") AS ?country)
    WHERE {{
      BIND(wd:{person_id} AS ?item)
      OPTIONAL {{
          ?item wdt:P21 ?sex_node.
          ?sex_node rdfs:label ?sex_label.
          FILTER(LANG(?sex_label) = \"en\")
      }}
      OPTIONAL {{ ?item wdt:P569 ?birthDate. }}
      OPTIONAL {{ ?item wdt:P570 ?deathDate. }}
      OPTIONAL {{
          ?item wdt:P106 ?occupation_node.
          ?occupation_node rdfs:label ?occupation_label.
          FILTER(LANG(?occupation_label) = \"en\")
      }}
      OPTIONAL {{
          ?item wdt:P27 ?country_node.
          ?country_node rdfs:label ?country_label.
          FILTER(LANG(?country_label) = \"en\")
      }}
    }}
    GROUP BY ?item
    """
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    try:
        response = requests.get(WIKIDATA_SPARQL_URL, headers=headers, params={'query': query, 'format': 'json'}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        bindings = response.json()['results']['bindings']
        if not bindings: return None
        details = bindings[0]
        return {
            'sex': details.get('sex', {}).get('value'),
            'dob': details.get('dob', {}).get('value'),
            'dod': details.get('dod', {}).get('value'),
            'occupations': details.get('occupations', {}).get('value'),
            'country': details.get('country', {}).get('value')
        }
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not fetch details for {person_id}. Error: {e}")
        return None

def fetch_and_insert_biographies(total_needed=3600):
    """Fetches biographies and structured data using the user-designed random-year-with-offset-memory strategy."""
    wiki_api = wikipediaapi.Wikipedia(USER_AGENT, 'en')
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(id) FROM {TABLE_NAME} WHERE sourcePersonaId LIKE 'wikidata_%'")
        count_in_db = cursor.fetchone()[0]
        
        remaining_needed = total_needed - count_in_db
        if remaining_needed <= 0:
            print(f"Database already contains {count_in_db} wikidata biographies.")
            return

        print(f"Database contains {count_in_db} records. Fetching {remaining_needed} more.")
        
        year_offsets = {}
        
        max_year = datetime.now().year - 18
        available_years = list(range(START_YEAR, max_year + 1))

        pbar = tqdm(total=remaining_needed, desc="Fetching Personas")
        
        while count_in_db < total_needed:
            if not available_years:
                print("\nAll available years have been exhausted. Stopping.")
                break

            year_to_query = random.choice(available_years)
            current_offset = year_offsets.get(year_to_query, 0)

            person_ids = get_person_ids_for_year(year_to_query, limit=BATCH_SIZE, offset=current_offset)
            
            year_offsets[year_to_query] = current_offset + BATCH_SIZE

            if len(person_ids) < BATCH_SIZE:
                available_years.remove(year_to_query)

            for person_info in person_ids:
                if count_in_db >= total_needed: break
                
                details = get_person_details(person_info['id'])
                if not details or not details.get('sex'):
                    continue

                page = wiki_api.page(person_info['title'])
                if page.exists() and page.namespace == 0 and page.text:
                    full_text = page.text
                    if len(full_text) < 200: continue

                    age = calculate_age(details['dob'], details['dod'])
                    if age is None:
                        continue
                        
                    source_id = f"wikidata_{person_info['title'].replace(' ', '_')[:20]}"
                    
                    sql = f"""INSERT INTO {TABLE_NAME} 
                           (sourcePersonaId, age, sex, occupation, native_country, persona_desc) 
                           VALUES (?, ?, ?, ?, ?, ?)
                           """
                    cursor.execute(sql, (
                        source_id, age, details['sex'], details['occupations'],
                        details['country'], full_text
                    ))
                    conn.commit()
                    count_in_db += 1
                    pbar.update(1)
            
            time.sleep(1)
        
        pbar.close()
    print("Successfully fetched and inserted all personas.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch random biographies and structured data from Wikidata/Wikipedia.")
    parser.add_argument("num", type=int, help="Total number of personas to ensure are in the database.")
    args = parser.parse_args()

    fetch_and_insert_biographies(total_needed=args.num)
