import os
import sys

# Running this as a script puts tools/pipeline/ (not the repo root) on sys.path, which hides
# asociety.*; the same bootstrap is in import_ess_human.py and value_pipeline.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from asociety.personality.qa_service import questionAnswerAll2, initializeQuestionAnswer
from asociety.repository.personality_rep import savePersonalities
from asociety.personality.personality_extractor import extract
if __name__ == "__main__":
    #generator:PersonaGenerator = PersonaGeneratorFactory.create()
    #print("Sampling personas...")
    #samples = generator.sampling(100)
    #print("Saving personas...")
    #savePersonas(samples)

    from asociety import config
    if len(sys.argv) < 2:
        raise SystemExit('usage: python tools/pipeline/pipeline.py <db_path>')
    config.verify_db_path(sys.argv[1])
    if config.configuration['request_method'] == 'question':

        print("Intializing question-answer table for all personas...")
        initializeQuestionAnswer()
        print("Answering questions for all personas...")
        questionAnswerAll2()

    else:
        from asociety.personality.quiz_service import create_tasks, execute_tasks
        print("Creating tasks for all personas...")
        create_tasks()
        print("Executing tasks for all personas...")
        execute_tasks()
    print("Extracting personalities...")
    ps = extract()
    print("Saving personalities...")
    savePersonalities(ps)
    print("Pipeline finished.")
