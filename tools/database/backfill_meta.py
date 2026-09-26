"""Move every experiment setting into each pipeline DB's `meta` table and drop the `model` column.

config.json is gone; each DB now describes its own run through a `meta` key/value table. This
backfill writes that table into every non-human pipeline DB and removes the write-only `model`
column from the results tables (personality / value / morality). The three `human.db`
baselines are left untouched: they are not pipeline DBs and keep their `model` columns.

A DB is a pipeline DB iff its `question` table holds 120 / 21 / 30 rows, so the instrument can be
derived. Everything else (seed.db, sampled_6000.db, real.db, agentic_society.db, …) is skipped.

Usage:
    python tools/database/backfill_meta.py             # backfill all three trees (idempotent)
    python tools/database/backfill_meta.py --dry-run   # print what would change, change nothing
    python tools/database/backfill_meta.py verify      # assert post-backfill invariants
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import sqlite3

DB_ROOT = os.path.join(ROOT, 'data', 'db')
TREES = ('personality', 'value', 'morality')

# Age-bucket CASE shared by all three persona_* views (mirrors the *_rep.py constants).
AGE_CASE = """CASE
   WHEN persona.age BETWEEN 16 AND 20 THEN '16_19'
  WHEN persona.age BETWEEN 20 AND 30 THEN '20_29'
  WHEN persona.age BETWEEN 30 AND 40 THEN '30_39'
  WHEN persona.age BETWEEN 40 AND 50 THEN '40_49'
  WHEN persona.age BETWEEN 50 AND 60 THEN '50_59'
  WHEN persona.age BETWEEN 60 AND 70 THEN '60_69'
  WHEN persona.age BETWEEN 70 AND 80 THEN '70_79'
  WHEN persona.age BETWEEN 80 AND 90 THEN '80_89'
  WHEN persona.age BETWEEN 90 AND 100 THEN '90_99'
  WHEN persona.age BETWEEN 100 AND 110 THEN '100_109'
END"""

# instrument -> (view name, results table)
VIEW = {
    'ipip_neo_120': ('persona_personality', 'personality'),
    'pvq_21': ('persona_value', 'value'),
    'mfq_30': ('persona_morality', 'morality'),
}

RESULTS_TABLES = ('personality', 'value', 'morality')
# qa_view is an IPIP-only view (joins question_answer + persona + question). It is unused by any
# code, and in a few personality DBs (nvadis-quiz, nvidia300) it dangles over a stripped
# question_answer table, which would make ALTER TABLE DROP COLUMN fail while SQLite re-parses the
# schema. Drop it with the rest; it is deliberately not recreated.
ALL_VIEWS = ('persona_personality', 'persona_value', 'persona_morality', 'qa_view')

META_KEYS = ('llm', 'request_method', 'question_prompt', 'persona_prompt', 'model')

_QUESTION_COUNT_TO_INSTRUMENT = {120: 'ipip_neo_120', 21: 'pvq_21', 30: 'mfq_30'}

# The paper's four population arms, which are the only value/morality DBs elicited question-by-
# question. Everything else in those two trees is the individual/sample batch, always the sheet
# method. Keyed relative to data/db/.
POPULATION = {
    'value/population/standard.db': ('question', 'question_prompt'),
    'value/population/antialign.db': ('question', 'question_prompt_antialign'),
    'value/population/narrative.db': ('sheet', 'sheet_prompt_narrative'),
    'value/population/wikifiction.db': ('sheet', 'sheet_prompt_wikifiction'),
    'morality/population/standard.db': ('question', 'question_prompt'),
    'morality/population/antialign.db': ('question', 'question_prompt_antialign'),
    'morality/population/narrative.db': ('sheet', 'sheet_prompt_narrative'),
    'morality/population/wikifiction.db': ('sheet', 'sheet_prompt_wikifiction'),
}


def view_ddl(name, table):
    return (f'CREATE VIEW "{name}" AS select\n {AGE_CASE} AS age_range,\n'
            f'persona.*, {table}.* from persona, {table} '
            f'where persona.id = {table}.persona_id')


def detect_variant(rel):
    r = rel.lower()
    if 'wikihuman' in r or 'wiki-human' in r:
        return 'wikihuman'
    if 'wikifiction' in r or 'wiki-fiction' in r:
        return 'wikifiction'
    if 'character' in r:
        return 'character'
    if 'narrative' in r or 'narra' in r:
        return 'narrative'
    if 'antialign' in r:
        return 'antialign'
    return 'plain'


def infer_method_prompt(rel, instrument, qa, quiz):
    """(request_method, question_prompt) for one DB, from content and driver knowledge."""
    if instrument in ('pvq_21', 'mfq_30'):
        if rel in POPULATION:
            return POPULATION[rel]
        # individual / sample batch: always sheet, narrative gets the novel prompt
        return ('sheet', 'sheet_prompt_narrative' if 'narrative' in rel else 'sheet_prompt')

    # personality: the method is recorded in the answer tables
    variant = detect_variant(rel)
    if qa and qa > 0:
        method = 'question'
    elif quiz and quiz > 0:
        method = 'sheet'
    else:
        method = 'sheet' if variant in ('narrative', 'wikifiction', 'wikihuman', 'character') \
            else 'question'
    if method == 'question':
        return ('question', 'question_prompt_antialign' if variant == 'antialign'
                else 'question_prompt')
    sheet = {
        'narrative': 'sheet_prompt_narrative',
        'wikifiction': 'sheet_prompt_wikifiction',
        'wikihuman': 'sheet_prompt_wikihuman',
        'character': 'sheet_prompt_character',
        'antialign': 'sheet_prompt_antialign',
        'plain': 'sheet_prompt',
    }[variant]
    return ('sheet', sheet)


def iter_dbs():
    """Yield (rel_path_from_data/db, abs_path) for every .db except the human baselines."""
    for tree in TREES:
        root = os.path.join(DB_ROOT, tree)
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if not name.endswith('.db') or name == 'human.db':
                    continue
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, DB_ROOT).replace(os.sep, '/')
                yield rel, path


def read_counts(path):
    con = sqlite3.connect(path)
    try:
        def count(table):
            try:
                return con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            except sqlite3.OperationalError:
                return None
        q = count('question')
        qa = count('question_answer')
        quiz = count('quiz_answer')
        cols = {}
        for t in RESULTS_TABLES:
            try:
                cols[t] = {r[1] for r in con.execute(f'PRAGMA table_info("{t}")')}
            except sqlite3.OperationalError:
                cols[t] = set()
        return q, qa, quiz, cols
    finally:
        con.close()


def backfill_one(rel, path, dry_run):
    q, qa, quiz, cols = read_counts(path)
    instrument = _QUESTION_COUNT_TO_INSTRUMENT.get(q)
    if instrument is None:
        return ('skip', f'{rel}: question={q} (no instrument)')

    method, prompt = infer_method_prompt(rel, instrument, qa, quiz)
    model_value = 'IPIP-NEO' if instrument == 'ipip_neo_120' else 'deepseek'
    meta = {
        'llm': 'deepseek',
        'request_method': method,
        'question_prompt': prompt,
        'persona_prompt': 'from_skeleton',
        'model': model_value,
    }

    drops = [t for t in RESULTS_TABLES if 'model' in cols.get(t, set())]
    view_name, view_table = VIEW[instrument]

    if dry_run:
        detail = f'meta={meta}, drop_model={drops}, view={view_name}'
        return ('would', f'{rel}: {detail}')

    con = sqlite3.connect(path)
    try:
        cur = con.cursor()
        for v in ALL_VIEWS:
            cur.execute(f'DROP VIEW IF EXISTS "{v}"')
        for t in drops:
            cur.execute(f'ALTER TABLE "{t}" DROP COLUMN model')
        cur.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)')
        for k, v in meta.items():
            cur.execute('INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)', (k, v))
        cur.execute(view_ddl(view_name, view_table))
        con.commit()
    finally:
        con.close()
    return ('done', f'{rel}: {method}/{prompt}, dropped {drops}, rewrote {view_name}')


def backfill(dry_run=False):
    done = would = skipped = 0
    for rel, path in iter_dbs():
        status, msg = backfill_one(rel, path, dry_run)
        print(f'  [{status}] {msg}')
        done += status == 'done'
        would += status == 'would'
        skipped += status == 'skip'
    print(f'\n{"would apply" if dry_run else "backfilled"}: {done + would}, skipped: {skipped}')


def verify():
    failures = []
    checked = 0
    for rel, path in iter_dbs():
        q, qa, quiz, cols = read_counts(path)
        instrument = _QUESTION_COUNT_TO_INSTRUMENT.get(q)
        if instrument is None:
            continue
        checked += 1
        con = sqlite3.connect(path)
        try:
            meta = {k: v for k, v in con.execute('SELECT key, value FROM meta')}
            missing = [k for k in META_KEYS if not meta.get(k)]
            if missing:
                failures.append(f'{rel}: meta missing {missing}')
            leaked = [t for t in RESULTS_TABLES if 'model' in cols.get(t, set())]
            if leaked:
                failures.append(f'{rel}: model column remains in {leaked}')
            view_name, _ = VIEW[instrument]
            has_view = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?", (view_name,)).fetchone()
            if not has_view:
                failures.append(f'{rel}: {view_name} view missing')
            if instrument == 'ipip_neo_120' and not rel.startswith('personality/'):
                failures.append(f'{rel}: instrument/tree mismatch')
            if instrument == 'pvq_21' and not rel.startswith('value/'):
                failures.append(f'{rel}: instrument/tree mismatch')
            if instrument == 'mfq_30' and not rel.startswith('morality/'):
                failures.append(f'{rel}: instrument/tree mismatch')
        finally:
            con.close()

    # human baselines must be untouched: still have the model column, no meta table
    for tree in TREES:
        h = os.path.join(DB_ROOT, tree, 'human.db')
        if not os.path.exists(h):
            continue
        con = sqlite3.connect(h)
        try:
            has_meta = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'").fetchone()
            if has_meta:
                failures.append(f'{tree}/human.db: unexpected meta table')
        finally:
            con.close()

    if failures:
        print('FAILURES:')
        for f in failures:
            print('  ' + f)
        sys.exit(1)
    print(f'OK: {checked} pipeline DBs have meta, no model column, correct view')


def main():
    args = [a for a in sys.argv[1:]]
    if 'verify' in args:
        verify()
        return
    dry_run = '--dry-run' in args
    backfill(dry_run)


if __name__ == '__main__':
    main()
