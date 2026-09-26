"""Run the PVQ pipeline over the four population-level value DBs in one process.

These are the paper's four arms (Standard / Antialign / Narrative / Wikifiction), the value-side
twins of the personality population DBs. Unlike the individual batch, the arms do not share a
request method: Standard and Antialign were elicited question-by-question (the personality twins
hold 74400 question_answer rows = 620 x 120), Narrative and Wikifiction sheet-by-sheet (3720 and
3600 quiz_answer rows = 620/600 x 6 sheets). Method AND prompt are read from each DB's `meta`
table by config.load_from_db, so the jobs here are just paths.

Usage:
    python tools/pipeline/run_value_population.py                 # all four arms
    python tools/pipeline/run_value_population.py <db> [<db> ...] # named arms, full paths
"""

import importlib
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

VALUE_ROOT = 'data/db/value/'
# order matches the paper: blue, red, green, orange, then the two external-persona arms.
JOBS = [
    VALUE_ROOT + 'population/standard.db',           # Standard
    VALUE_ROOT + 'population/antialign.db',          # Antialign
    VALUE_ROOT + 'population/narrative.db',          # Narrative
    VALUE_ROOT + 'population/wikifiction.db',        # Wikifiction
    VALUE_ROOT + 'population/thinkpersona.db',       # ThinkPersona
    VALUE_ROOT + 'population/real-persona-chat.db',  # real-persona-chat
]


def db_file(db_path):
    return os.path.join(ROOT, *db_path.split('/'))


def scored_rows(db_path):
    con = sqlite3.connect(db_file(db_path))
    try:
        return con.execute('SELECT COUNT(*) FROM value').fetchone()[0]
    finally:
        con.close()


def run_one(db_path):
    from asociety import config
    from asociety.repository.value_rep import saveValues

    value_extractor = importlib.import_module('asociety.value.value_extractor')

    config.load_from_db(db_path)

    if config.configuration['request_method'] == 'question':
        qa = importlib.import_module('asociety.personality.qa_service')
        qa.initializeQuestionAnswer()
        qa.questionAnswerAll2()
    else:
        quiz_service = importlib.import_module('asociety.personality.quiz_service')
        quiz_service.create_tasks()
        quiz_service.execute_tasks()

    saveValues(value_extractor.extract())


def summarize(db_path):
    con = sqlite3.connect(db_file(db_path))
    try:
        personas = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
        scored = con.execute('SELECT COUNT(*) FROM value').fetchone()[0]
        cols = ['self_direction', 'power', 'universalism', 'achievement', 'security',
                'stimulation', 'conformity', 'tradition', 'hedonism', 'benevolence',
                'openness_to_change', 'self_enhancement', 'self_transcendence', 'conservation']
        unscored = con.execute('SELECT COUNT(*) FROM value WHERE ' + ' OR '.join(
            f'{c} IS NULL' for c in cols)).fetchone()[0]
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
