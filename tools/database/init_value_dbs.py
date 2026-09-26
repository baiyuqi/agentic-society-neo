"""Split data/db into a personality/ tree and a value/ tree, then strip the value DBs.

The value experiment reuses the personas from the personality experiment but must not
carry any IPIP rows, so each copied DB is reduced to its persona tables and given clean
empty shells for the tables the pipeline will rebuild.

Usage:
    python tools/database/init_value_dbs.py split     # move + copy (non-destructive to personality/)
    python tools/database/init_value_dbs.py strip     # drop IPIP tables/views, rebuild shells, vacuum
    python tools/database/init_value_dbs.py views     # create the value table + persona_value view
    python tools/database/init_value_dbs.py items     # load the 21 PVQ items into every question table
    python tools/database/init_value_dbs.py verify    # assert post-strip invariants
    python tools/database/init_value_dbs.py all
"""

import os
import shutil
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_ROOT = os.path.join(ROOT, 'data', 'db')
PERSONALITY_ROOT = os.path.join(DB_ROOT, 'personality')
VALUE_ROOT = os.path.join(DB_ROOT, 'value')

# Paper-relevant DBs, expressed relative to both trees -- the layout is mirrored so a
# personality path maps to its value twin by swapping one path segment.
VALUE_MANIFEST = [
    # the six population arms
    'population/standard.db',
    'population/antialign.db',
    'population/narrative.db',
    'population/wikifiction.db',
    'population/thinkpersona.db',
    'population/real-persona-chat.db',
    # individual single-persona experiment: 5 personas x 3 methods
    *[f'individual/persona{i}/{method}.db'
      for i in range(1, 6) for method in ('standard', 'narrative', 'poor')],
]

# IPIP-only objects. The persona tables are never touched.
DROP_TABLES = ['personality', 'personality_analysis', 'question', 'question_answer',
               'quiz_answer', 'quiz_sheet', 'samples']
DROP_VIEWS = ['persona_personality', 'qa_view']
LEGACY_LIKE = "name LIKE '\\_question\\_answer\\_old%' ESCAPE '\\'"

KEEP_TABLES = {'persona', 'skeleton_persona'}

# quiz_service.create_sheets() resets the sheet auto-increment counter via
# "DELETE FROM sqlite_sequence", which only exists if a table uses AUTOINCREMENT. The
# personality tree's quiz_sheet is declared that way; the ORM would emit a plain
# INTEGER PRIMARY KEY, so rebuild it here to keep the two trees schema-identical.
QUIZ_SHEET_DDL = """CREATE TABLE quiz_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sheet TEXT
            )"""


def _normalize_quiz_sheet(con):
    ddl = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='quiz_sheet'").fetchone()
    if ddl and 'AUTOINCREMENT' in ddl[0]:
        return False
    con.execute('DROP TABLE IF EXISTS quiz_sheet')
    con.execute(QUIZ_SHEET_DDL)
    return True


def _add_source_persona_id(con):
    """Add persona.sourcePersonaId to the archived DBs that predate the column.

    The old persona table carries six census columns the ORM dropped and lacks
    sourcePersonaId, so `session.query(Persona)` -- which expands to every declared
    column -- dies with "no such column: persona.sourcePersonaId". Only the value tree
    is normalized: the personality tree's copies are finished archives and stay as they
    are. The column is nullable and records provenance ("{id}@skeleton"), so NULL is a
    faithful stand-in for rows written before it existed.
    """
    names = [row[1] for row in con.execute('PRAGMA table_info(persona)')]
    if not names or 'sourcePersonaId' in names:
        return False
    con.execute('ALTER TABLE persona ADD COLUMN sourcePersonaId VARCHAR(30)')
    return True


def move_into_personality():
    os.makedirs(PERSONALITY_ROOT, exist_ok=True)
    os.makedirs(VALUE_ROOT, exist_ok=True)
    here = {os.path.normcase(PERSONALITY_ROOT), os.path.normcase(VALUE_ROOT)}
    moved = 0
    for name in os.listdir(DB_ROOT):
        src = os.path.join(DB_ROOT, name)
        if os.path.normcase(src) in here:
            continue
        dst = os.path.join(PERSONALITY_ROOT, name)
        if os.path.exists(dst):
            print(f'  skip (already in personality/): {name}')
            continue
        shutil.move(src, dst)
        moved += 1
        print(f'  moved {name}')
    print(f'personality/: {moved} entries moved')


def copy_value_manifest():
    copied = skipped = 0
    for rel in VALUE_MANIFEST:
        src = os.path.join(PERSONALITY_ROOT, *rel.split('/'))
        dst = os.path.join(VALUE_ROOT, *rel.split('/'))
        if not os.path.exists(src):
            print(f'  MISSING source, skipping: {rel}')
            continue
        size = os.path.getsize(src)
        if size == 0:
            print(f'  zero-byte source, skipping: {rel}')
            continue
        # Existence, not size: strip() shrinks the value copy, so a size comparison would
        # re-copy (and un-strip) the whole tree on every `split` re-run.
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            skipped += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        print(f'  copied {rel} ({size / 1e6:.1f} MB)')
    print(f'value/: {copied} copied, {skipped} already up to date')


def _connect(path):
    con = sqlite3.connect(path)
    con.execute('PRAGMA journal_mode=DELETE')
    return con


def strip_value_db(path, root=VALUE_ROOT, drop_tables=DROP_TABLES, drop_views=DROP_VIEWS):
    """Drop one instrument's tables and views from a copied DB and rebuild clean empty shells.

    `root` only affects the relative path in the progress line. The drop lists default to the value
    tree's; a caller building another instrument's tree passes its own (it also has to drop the
    instrument tables a previously-opened DB may have gained).
    """
    size_before = os.path.getsize(path)
    con = sqlite3.connect(path)
    try:
        personas_before = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
        descs_before = con.execute(
            'SELECT COUNT(*) FROM persona WHERE persona_desc IS NOT NULL').fetchone()[0]
    finally:
        con.close()

    con = _connect(path)
    try:
        cur = con.cursor()
        for name in drop_tables:
            cur.execute(f'DROP TABLE IF EXISTS "{name}"')
        # fetchall first: dropping mutates sqlite_master and would truncate a live cursor
        legacy = cur.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND {LEGACY_LIKE}").fetchall()
        for (name,) in legacy:
            cur.execute(f'DROP TABLE IF EXISTS "{name}"')
            print(f'    dropped legacy table {name}')
        for name in drop_views:
            cur.execute(f'DROP VIEW IF EXISTS "{name}"')
        con.commit()
    finally:
        con.close()

    from asociety.repository.database import create_tables, set_currentdb
    set_currentdb(os.path.relpath(path, ROOT).replace('\\', '/'))
    create_tables()
    normalize_schema(path)

    con = sqlite3.connect(path)
    con.isolation_level = None
    con.execute('VACUUM')
    con.close()

    for suffix in ('-wal', '-shm'):
        sidecar = path + suffix
        if os.path.exists(sidecar):
            os.remove(sidecar)

    con = sqlite3.connect(path)
    try:
        personas_after = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
        descs_after = con.execute(
            'SELECT COUNT(*) FROM persona WHERE persona_desc IS NOT NULL').fetchone()[0]
    finally:
        con.close()
    if (personas_before, descs_before) != (personas_after, descs_after):
        raise AssertionError(
            f'{path}: personas changed {personas_before}->{personas_after}, '
            f'persona_desc {descs_before}->{descs_after}')

    size_after = os.path.getsize(path)
    print(f'  {os.path.relpath(path, root)}: '
          f'{size_before / 1e6:.1f} MB -> {size_after / 1e6:.2f} MB, '
          f'{personas_after} personas ({descs_after} with persona_desc)')


# The human baseline is not a pipeline DB: it is built by tools/importers/import_ess_human.py
# and holds only persona + value + persona_value, so it is excluded from the pipeline-DB
# functions below (strip, views, the schema invariant) and checked separately.
HUMAN_DB = os.path.join(VALUE_ROOT, 'human.db')


def value_db_paths():
    paths = []
    for dirpath, _dirnames, filenames in os.walk(VALUE_ROOT):
        for name in filenames:
            if name.endswith('.db'):
                paths.append(os.path.join(dirpath, name))
    return sorted(p for p in paths if os.path.normcase(p) != os.path.normcase(HUMAN_DB))


def strip_all():
    paths = value_db_paths()
    if not paths:
        print('no value DBs found -- run split first')
        return
    for path in paths:
        print(f'stripping {os.path.relpath(path, VALUE_ROOT)}')
        strip_value_db(path)
    print(f'stripped {len(paths)} value DBs')


def normalize_schema(path):
    """Make a value DB match the schema the ORM expects.

    Two fixes: quiz_sheet back to the personality tree's AUTOINCREMENT shape, and
    persona.sourcePersonaId added to the archived DBs that predate the column. Both are
    idempotent, so this is safe to re-run over an already-normalized tree.
    """
    con = sqlite3.connect(path)
    try:
        changed = _normalize_quiz_sheet(con)
        changed = _add_source_persona_id(con) or changed
        con.commit()
    finally:
        con.close()
    return changed


def ensure_value_schema():
    """Create the value table + persona_value view and normalize quiz_sheet in every DB."""
    from asociety.repository.database import create_tables, set_currentdb
    from asociety.repository.value_rep import create_value_view
    paths = value_db_paths()
    if not paths:
        print('no value DBs found -- run split first')
        return
    for path in paths:
        set_currentdb(os.path.relpath(path, ROOT).replace('\\', '/'))
        create_tables()
        create_value_view()
        normalize_schema(path)
        print(f'  {os.path.relpath(path, VALUE_ROOT)}')
    print(f'value schema + persona_value view ensured in {len(paths)} DBs')


def prepare_sheets(path):
    """Materialize the quiz_sheet rows after the question items are loaded.

    The sheet content is a pure function of the question table + the instrument's sheet_size, so a
    run-ready DB carries it; the pipeline only runs create_tasks + execute_tasks. load_from_db
    derives the instrument from the question count already loaded by `items`.
    """
    from asociety import config
    from asociety.personality.quiz_service import create_sheets
    config.load_from_db(os.path.relpath(path, ROOT).replace('\\', '/'))
    create_sheets()


def load_items():
    """Put the 21 PVQ items and their quiz sheet into every value DB, so a run starts ready."""
    from asociety.repository.database import set_currentdb
    from tools.importers.import_pvq_set import import_pvq_set
    paths = value_db_paths()
    if not paths:
        print('no value DBs found -- run split first')
        return
    for path in paths:
        set_currentdb(os.path.relpath(path, ROOT).replace('\\', '/'))
        print(f'  {os.path.relpath(path, VALUE_ROOT)}')
        import_pvq_set()
        prepare_sheets(path)
    print(f'PVQ items + sheets loaded into {len(paths)} value DBs')


def verify_human_db():
    """The ESS baseline: every persona scored on all 14 values, nothing else required."""
    from asociety.repository.value_rep import ALL_VALUE_COLUMNS
    if not os.path.exists(HUMAN_DB):
        print('  human.db: absent (run: python tools/importers/import_ess_human.py)')
        return []

    con = sqlite3.connect(HUMAN_DB)
    try:
        failures = []
        personas = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
        scored = con.execute('SELECT COUNT(*) FROM value').fetchone()[0]
        if personas == 0 or scored != personas:
            failures.append(f'human.db: {personas} personas but {scored} scored rows')
        unscored = con.execute(
            'SELECT COUNT(*) FROM value WHERE ' +
            ' OR '.join(f'{c} IS NULL' for c in ALL_VALUE_COLUMNS)).fetchone()[0]
        if unscored:
            failures.append(f'human.db: {unscored} rows with a null value column')
        aged = con.execute(
            "SELECT COUNT(*) FROM persona_value WHERE age_range IS NOT NULL").fetchone()[0]
        if aged != personas:
            failures.append(f'human.db: {personas - aged} personas fall outside the age buckets')
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            failures.append(f'human.db: integrity_check={integrity}')
        print(f'  human.db: {personas} personas scored on {len(ALL_VALUE_COLUMNS)} values')
        return failures
    finally:
        con.close()


def verify():
    from asociety.value import pvq
    expected_items = len(pvq.question_ids())
    failures = []
    for path in value_db_paths():
        rel = os.path.relpath(path, VALUE_ROOT)
        con = sqlite3.connect(path)
        try:
            objects = {name: kind for name, kind in
                       con.execute('SELECT name, type FROM sqlite_master')}
            tables = {n for n, k in objects.items() if k == 'table'}
            views = {n for n, k in objects.items() if k == 'view'}

            missing = KEEP_TABLES - tables
            if missing:
                failures.append(f'{rel}: missing persona tables {missing}')
            leaked = [n for n in objects if '_question_answer_old' in n]
            if leaked:
                failures.append(f'{rel}: legacy tables remain {leaked}')
            if 'persona_personality' in views:
                failures.append(f'{rel}: persona_personality view remains')
            if 'value' not in tables:
                failures.append(f'{rel}: missing value table (run: views)')
            if 'persona_value' not in views:
                failures.append(f'{rel}: missing persona_value view (run: views)')

            sheet_ddl = con.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='quiz_sheet'"
            ).fetchone()
            if sheet_ddl and 'AUTOINCREMENT' not in sheet_ddl[0]:
                failures.append(f'{rel}: quiz_sheet lacks AUTOINCREMENT '
                                f'(create_sheets would fail on sqlite_sequence)')

            if 'persona' not in tables:
                failures.append(f'{rel}: no persona table')
                continue
            personas = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
            if personas == 0:
                failures.append(f'{rel}: persona table is empty')

            persona_cols = {row[1] for row in con.execute('PRAGMA table_info(persona)')}
            if 'sourcePersonaId' not in persona_cols:
                failures.append(f'{rel}: persona lacks sourcePersonaId '
                                f'(session.query(Persona) would fail)')

            for name in DROP_TABLES:
                # `question` is dropped by strip and then refilled by `items`, so unlike the
                # other IPIP tables it is not required to stay empty; checked below instead.
                if name in tables and name != 'question':
                    n = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    if n:
                        failures.append(f'{rel}: {name} still holds {n} rows')

            items = con.execute('SELECT COUNT(*) FROM question').fetchone()[0] \
                if 'question' in tables else 0
            if items != expected_items:
                failures.append(f'{rel}: question holds {items} rows, expected {expected_items} '
                                f'(run: python tools/database/init_value_dbs.py items)')

            sheets = con.execute('SELECT COUNT(*) FROM quiz_sheet').fetchone()[0] \
                if 'quiz_sheet' in tables else 0
            if sheets != 1:
                failures.append(f'{rel}: quiz_sheet holds {sheets} rows, expected 1 '
                                f'(run: python tools/database/init_value_dbs.py items)')

            integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity != 'ok':
                failures.append(f'{rel}: integrity_check={integrity}')

            print(f'  {rel}: {personas} personas, tables={sorted(tables)}, views={sorted(views)}')
        finally:
            con.close()

    failures += verify_human_db()

    if failures:
        print('\nFAILURES:')
        for f in failures:
            print('  ' + f)
        sys.exit(1)
    print(f'\nOK: {len(value_db_paths())} value DBs clean')


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'all'
    sys.path.insert(0, ROOT)
    if action in ('split', 'all'):
        print('== split ==')
        move_into_personality()
        copy_value_manifest()
    if action in ('strip', 'all'):
        print('== strip ==')
        strip_all()
    if action in ('views', 'all'):
        print('== views ==')
        ensure_value_schema()
    if action in ('items', 'all'):
        print('== items ==')
        load_items()
    if action in ('verify', 'all'):
        print('== verify ==')
        verify()


if __name__ == '__main__':
    main()
