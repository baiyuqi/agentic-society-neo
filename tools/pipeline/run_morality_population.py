"""Run the MFQ pipeline over the four population-level morality DBs in one process.

These are the paper's four arms (Standard / Antialign / Narrative / Wikifiction), the morality-side
twins of the personality and value population DBs. Unlike the individual batch, the arms do not
share a request method: Standard and Antialign are elicited question-by-question (the personality
twins hold 74400 question_answer rows = 620 x 120), Narrative and Wikifiction sheet-by-sheet (3720
and 3600 quiz_answer rows = 620/600 x 6 sheets). Method AND prompt are read from each DB's `meta`
table by config.load_from_db, so the jobs here are just paths.

Usage:
    python tools/pipeline/run_morality_population.py                 # all four arms
    python tools/pipeline/run_morality_population.py <db> [<db> ...] # named arms, full paths
"""

import importlib
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

MORALITY_ROOT = 'data/db/morality/'
# order matches the paper: blue, red, green, orange, then the two external-persona arms.
JOBS = [
    MORALITY_ROOT + 'population/standard.db',           # Standard
    MORALITY_ROOT + 'population/antialign.db',          # Antialign
    MORALITY_ROOT + 'population/narrative.db',          # Narrative
    MORALITY_ROOT + 'population/wikifiction.db',        # Wikifiction
    MORALITY_ROOT + 'population/thinkpersona.db',       # ThinkPersona
    MORALITY_ROOT + 'population/real-persona-chat.db',  # real-persona-chat
]


def db_file(db_path):
    return os.path.join(ROOT, *db_path.split('/'))


def scored_rows(db_path):
    con = sqlite3.connect(db_file(db_path))
    try:
        return con.execute('SELECT COUNT(*) FROM morality').fetchone()[0]
    finally:
        con.close()


def run_one(db_path):
    from asociety import config
    from asociety.repository.moral_rep import saveMorality

    morality_extractor = importlib.import_module('asociety.morality.morality_extractor')

    config.load_from_db(db_path)

    if config.configuration['request_method'] == 'question':
        qa = importlib.import_module('asociety.personality.qa_service')
        qa.initializeQuestionAnswer()
        qa.questionAnswerAll2()
    else:
        quiz_service = importlib.import_module('asociety.personality.quiz_service')
        quiz_service.create_tasks()
        quiz_service.execute_tasks()

    saveMorality(morality_extractor.extract())


def summarize(db_path):
    from asociety.repository.moral_rep import ALL_MORALITY_COLUMNS
    con = sqlite3.connect(db_file(db_path))
    try:
        personas = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
        scored = con.execute('SELECT COUNT(*) FROM morality').fetchone()[0]
        unscored = con.execute('SELECT COUNT(*) FROM morality WHERE ' + ' OR '.join(
            f'{c} IS NULL' for c in ALL_MORALITY_COLUMNS)).fetchone()[0]
        return personas, scored, unscored
    finally:
        con.close()


def main():
    if sys.argv[1:]:
        wanted = set(sys.argv[1:])
        jobs = [j for j in JOBS if j in wanted]
        missing = wanted - set(JOBS)
        if missing:
            raise SystemExit(f'not a population arm: {sorted(missing)}')
    else:
        jobs = JOBS
    print(f'{len(jobs)} arm(s) to run\n')

    skipped, done = [], []
    for db_path in jobs:
        if scored_rows(db_path) > 0:
            print(f'SKIP {db_path}: already scored')
            skipped.append(db_path)
            continue
        print(f'== {db_path} ==')
        run_one(db_path)
        personas, scored, unscored = summarize(db_path)
        print(f'   personas={personas} scored={scored} unscored={unscored}\n')
        done.append(db_path)

    print(f'finished: {len(done)} run, {len(skipped)} skipped')
    for db_path in done:
        personas, scored, unscored = summarize(db_path)
        print(f'  {db_path:<48} {scored}/{personas} scored, {unscored} unscored')


if __name__ == '__main__':
    main()
