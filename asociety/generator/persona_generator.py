import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from langchain_core.output_parsers import StrOutputParser
from asociety.generator.llm_engine import llm, from_skeleton
from asociety.repository.persona_rep import get_unprocessed_skeletons, save_enriched_persona

output_parser = StrOutputParser()
chain = from_skeleton | llm | output_parser

class PersonaGenerator:
    def __init__(self) -> None:
        self.enricher = chain

    def enrich_unprocessed_skeletons(self, max_workers=15):
        """
        Scans the database for unprocessed skeletons, enriches them using an LLM in parallel,
        and saves the complete, enriched data to the 'persona' table.
        A progress bar is displayed in the console.
        """
        print("Scanning for unprocessed skeletons...")
        
        unprocessed = get_unprocessed_skeletons()
        
        if not unprocessed:
            print("No unprocessed skeletons found.")
            return
            
        print(f"Found {len(unprocessed)} skeletons to enrich.")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a future for each skeleton enrichment
            futures = {executor.submit(self._enrich_and_save, skeleton): skeleton for skeleton in unprocessed}
            
            # Process futures as they complete, with a progress bar
            for future in tqdm(as_completed(futures), total=len(unprocessed), desc="Enriching skeletons"):
                skeleton_id = futures[future]['id']
                try:
                    future.result()  # Get result to raise any exceptions
                except Exception as e:
                    print(f"Error enriching skeleton ID {skeleton_id}: {e}")

    def _enrich_and_save(self, skeleton: dict):
        """
        Enriches a single skeleton and saves it to the database.
        This method is designed to be called by the thread pool.
        """
        # 1. Enrich the skeleton data
        persona_desc = self.llm_enrich(skeleton)
        
        # 2. Add the new description to the skeleton dictionary
        skeleton['persona_desc'] = persona_desc
        
        # 3. Save the complete persona object
        save_enriched_persona(skeleton)

    def llm_enrich(self, skel: dict) -> str:
        """Invokes the LLM chain to get a persona description from a skeleton dictionary."""
        persona_json_str = json.dumps(skel)
        enriched_description = self.enricher.invoke({persona_json_str})
        return enriched_description

class PersonaGeneratorFactory:
    @staticmethod
    def create():
        return PersonaGenerator()