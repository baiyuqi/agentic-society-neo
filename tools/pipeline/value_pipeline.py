import os
import sys

# Running this as a script puts tools/pipeline/ (not the repo root) on sys.path, which hides
# both asociety.* and tools.importers.*; the same bootstrap is in import_ess_human.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from asociety.personality.qa_service import questionAnswerAll2, initializeQuestionAnswer
from asociety.repository.value_rep import saveValues
from asociety.value.value_extractor import extract
if __name__ == "__main__":
    from asociety import config

    if len(sys.argv) < 2:
        raise SystemExit('usage: python tools/pipeline/value_pipeline.py <db_path>')
    config.verify_db_path(sys.argv[1])

    # The 21 PVQ items are normally already in place ("init_value_dbs.py items" loads them into
    # every value DB). This is the belt-and-braces path for a DB that has not been through it:
    # import_pvq_set is a no-op once the items are there, and refuses a partial set otherwise.
    from tools.importers.import_pvq_set import import_pvq_set
    import_pvq_set()

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
    print("Extracting values...")
    vs = extract()
    print("Saving values...")
    saveValues(vs)
    print("Pipeline finished.")
