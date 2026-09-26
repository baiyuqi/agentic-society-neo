"""Run the MFQ pipeline over a list of morality DBs in one process.

morality_pipeline.py drives a single DB. This drives a batch instead, loading each DB's settings
(method + prompt) from its `meta` table via config.load_from_db, so no config.json and no in-memory
monkeypatching is needed.

Usage:
    python tools/pipeline/run_morality_batch.py                 # every individual DB
    python tools/pipeline/run_morality_batch.py <db> [<db> ...]  # named DBs
"""

import importlib
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

INDIVIDUAL_ROOT = os.path.join('data', 'db', 'morality', 'individual')
# persona5 has no narrative DB; the existence test below simply will not find one.
METHODS = ('standard', 'poor', 'narrative')


def default_jobs():
    jobs = []
    for persona in range(1, 6):
        for method in METHODS:
            rel = f'persona{persona}/{method}.db'
            if os.path.exists(os.path.join(ROOT, *INDIVIDUAL_ROOT.split('/'), *rel.split('/'))):
                jobs.append(f'{INDIVIDUAL_ROOT}/{rel}')
    return jobs


def scored_rows(db_path):
    con = sqlite3.connect(os.path.join(ROOT, *db_path.split('/')))
    try:
        return con.execute('SELECT COUNT(*) FROM morality').fetchone()[0]
    finally:
        con.close()


def run_one(db_path):
    from asociety import config
    from asociety.repository.moral_rep import saveMorality

    quiz_service = importlib.import_module('asociety.personality.quiz_service')
    morality_extractor = importlib.import_module('asociety.morality.morality_extractor')

    config.load_from_db(db_path)

    quiz_service.create_tasks()
    quiz_service.execute_tasks()
    saveMorality(morality_extractor.extract())


def summarize(db_path):
    from asociety.repository.moral_rep import ALL_MORALITY_COLUMNS
    con = sqlite3.connect(os.path.join(ROOT, *db_path.split('/')))
    try:
        personas = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
        scored = con.execute('SELECT COUNT(*) FROM morality').fetchone()[0]
        unscored = con.execute('SELECT COUNT(*) FROM morality WHERE ' + ' OR '.join(
            f'{c} IS NULL' for c in ALL_MORALITY_COLUMNS)).fetchone()[0]
        return personas, scored, unscored
    finally:
        con.close()


def main():
    jobs = [a for a in sys.argv[1:]] or default_jobs()
    print(f'{len(jobs)} DB(s) to run\n')

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
        print(f'  {db_path:<60} {scored}/{personas} scored, {unscored} unscored')


if __name__ == '__main__':
    main()
