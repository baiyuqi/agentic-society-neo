"""
Persona Manager Module

This module provides functionality to enrich existing skeleton personas
in the database that do not yet have a full persona description.
"""

import json
from asociety.generator.llm_engine import llm, from_skeleton
from asociety.repository.persona_rep import get_unprocessed_skeletons, save_enriched_persona
from langchain_core.output_parsers import StrOutputParser

# Setup the LLM chain for enrichment
enricher_chain = from_skeleton | llm | StrOutputParser()

def enrich_unprocessed_personas() -> int:
    """
    Scans the current database for skeletons without a corresponding persona,
    enriches them using an LLM, and saves them to the 'persona' table.

    Returns:
        int: Number of personas successfully enriched.
    """
    # Get skeletons that don't have a corresponding entry in the persona table
    skeletons_to_process = get_unprocessed_skeletons()

    if not skeletons_to_process:
        print("No unprocessed skeletons found.")
        return 0

    print(f"Found {len(skeletons_to_process)} skeletons to enrich.")
    enriched_count = 0

    for skeleton in skeletons_to_process:
        try:
            # Enrich skeleton using the LLM chain
            enriched_desc = _llm_enrich_skeleton(skeleton)

            # Add the new description to the skeleton data
            skeleton['persona_desc'] = enriched_desc
            
            # Save the complete, enriched data as a new entry in the 'persona' table
            save_enriched_persona(skeleton)
            enriched_count += 1
            print(f"Successfully enriched and saved persona for skeleton ID: {skeleton['id']}")

        except Exception as e:
            print(f"Failed to enrich skeleton ID {skeleton.get('id', 'N/A')}: {e}")
            # Continue with the next skeleton if one fails
            continue

    return enriched_count

def _llm_enrich_skeleton(skeleton_dict: dict) -> str:
    """
    Uses the LLM to enrich a persona skeleton into a full description.
    
    Args:
        skeleton_dict: Dictionary containing persona skeleton data.
    
    Returns:
        str: Generated persona description.
    """
    try:
        # The chain expects the skeleton to be a JSON string
        persona_json = json.dumps(skeleton_dict, ensure_ascii=False)
        
        # Invoke the chain to generate the description
        enriched_desc = enricher_chain.invoke({"skeleton": persona_json})
        
        return enriched_desc
        
    except Exception as e:
        # Re-raise the exception to be caught by the calling function
        raise Exception(f"LLM generation failed: {str(e)}")

