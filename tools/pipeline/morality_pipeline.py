import os
import sys

# Running this as a script puts tools/pipeline/ (not the repo root) on sys.path, which hides
# both asociety.* and tools.importers.*; the same bootstrap is in import_mfq_set.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from asociety.personality.qa_service import questionAnswerAll2, initializeQuestionAnswer
from asociety.repository.moral_rep import saveMorality
from asociety.morality.morality_extractor import extract

if __name__ == "__main__":
    from asociety import config

    if len(sys.argv) < 2:
        raise SystemExit('usage: python tools/pipeline/morality_pipeline.py <db_path>')
    config.verify_db_path(sys.argv[1])

    # The 30 MFQ items are normally already in place ("init_morality_dbs.py items" loads them into
    # every morality DB). This is the belt-and-braces path for a DB that has not been through it:
    # import_mfq_set is a no-op once the items are there, and refuses a partial set otherwise.
    from tools.importers.import_mfq_set import import_mfq_set
    import_mfq_set()

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
    print("Extracting moral foundations...")
    ms = extract()
    print("Saving moral foundations...")
    saveMorality(ms)
    print("Pipeline finished.")
