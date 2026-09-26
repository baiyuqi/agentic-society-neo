"""Copy the paper DBs from the personality tree into a morality/ tree, then strip them.

The morality experiment reuses the personas from the personality experiment but must not carry any
IPIP or PVQ rows, so each copied DB is reduced to its persona tables and given clean empty shells
for the tables the pipeline will rebuild.

This is the morality counterpart of init_value_dbs.py and reuses its manifest and strip machinery.
Two things differ: there is no `split` step (data/db is already split into the two trees, so moving
`move_into_personality` again would relocate data/db/morality into data/db/personality), and there
is no human baseline (no open age-stratified MFQ norm sample), so no human.db handling.

Usage:
    python tools/database/init_morality_dbs.py copy    # personality/ -> morality/
    python tools/database/init_morality_dbs.py strip   # drop instrument tables/views, rebuild shells
    python tools/database/init_morality_dbs.py views   # create the morality table + persona_morality view
    python tools/database/init_morality_dbs.py items   # load the 30 MFQ items into every question table
    python tools/database/init_morality_dbs.py verify  # assert post-strip invariants
    python tools/database/init_morality_dbs.py all
"""

import os
import shutil
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.database.init_value_dbs import (  # noqa: E402
    DB_ROOT, KEEP_TABLES, PERSONALITY_ROOT, VALUE_MANIFEST, normalize_schema, prepare_sheets,
    strip_value_db,
)

MORALITY_ROOT = os.path.join(DB_ROOT, 'morality')

# Same paper DBs as the value tree -- the layout is mirrored across all three trees.
MORALITY_MANIFEST = VALUE_MANIFEST

# The value strip's lists plus the other instruments' tables and views: the studio has already
# opened personality-tree DBs, so create_tables()/create_value_view() may have left empty
# value/morality shells and a persona_value view in the copies.
DROP_TABLES = ['personality', 'personality_analysis', 'question', 'question_answer',
               'quiz_answer', 'quiz_sheet', 'samples', 'value', 'morality']
DROP_VIEWS = ['persona_personality', 'qa_view', 'persona_value', 'persona_morality']


def copy_manifest():
    copied = skipped = 0
    for rel in MORALITY_MANIFEST:
        src = os.path.join(PERSONALITY_ROOT, *rel.split('/'))
        dst = os.path.join(MORALITY_ROOT, *rel.split('/'))
        if not os.path.exists(src):
            print(f'  MISSING source, skipping: {rel}')
            continue
        size = os.path.getsize(src)
        if size == 0:
            print(f'  zero-byte source, skipping: {rel}')
            continue
        # Existence, not size: strip() shrinks the copy, so a size comparison would re-copy (and
        # un-strip) the whole tree on every `copy` re-run.
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            skipped += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        print(f'  copied {rel} ({size / 1e6:.1f} MB)')
    print(f'morality/: {copied} copied, {skipped} already up to date')


def morality_db_paths():
    paths = []
    for dirpath, _dirnames, filenames in os.walk(MORALITY_ROOT):
        for name in filenames:
            if name.endswith('.db'):
                paths.append(os.path.join(dirpath, name))
    return sorted(paths)


def strip_all():
    paths = morality_db_paths()
    if not paths:
        print('no morality DBs found -- run copy first')
        return
    for path in paths:
        print(f'stripping {os.path.relpath(path, MORALITY_ROOT)}')
        strip_value_db(path, root=MORALITY_ROOT, drop_tables=DROP_TABLES, drop_views=DROP_VIEWS)
    print(f'stripped {len(paths)} morality DBs')


def ensure_morality_schema():
    """Create the morality table + persona_morality view and normalize quiz_sheet in every DB."""
    from asociety.repository.database import create_tables, set_currentdb
    from asociety.repository.moral_rep import create_morality_view
    paths = morality_db_paths()
    if not paths:
        print('no morality DBs found -- run copy first')
        return
    for path in paths:
        set_currentdb(os.path.relpath(path, ROOT).replace('\\', '/'))
        create_tables()
        create_morality_view()
        normalize_schema(path)
        print(f'  {os.path.relpath(path, MORALITY_ROOT)}')
    print(f'morality schema + persona_morality view ensured in {len(paths)} DBs')


def load_items():
    """Put the 30 MFQ items and their quiz sheet into every morality DB, so a run starts ready."""
    from asociety.repository.database import set_currentdb
    from tools.importers.import_mfq_set import import_mfq_set
    paths = morality_db_paths()
    if not paths:
        print('no morality DBs found -- run copy first')
        return
    for path in paths:
        set_currentdb(os.path.relpath(path, ROOT).replace('\\', '/'))
        print(f'  {os.path.relpath(path, MORALITY_ROOT)}')
        import_mfq_set()
        prepare_sheets(path)
    print(f'MFQ items + sheets loaded into {len(paths)} morality DBs')


def verify():
    from asociety.morality import mfq
    expected_items = len(mfq.question_ids())
    failures = []
    for path in morality_db_paths():
        rel = os.path.relpath(path, MORALITY_ROOT)
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
            for view in ('persona_personality', 'persona_value'):
                if view in views:
                    failures.append(f'{rel}: {view} view remains')
            if 'morality' not in tables:
                failures.append(f'{rel}: missing morality table (run: views)')
            if 'persona_morality' not in views:
                failures.append(f'{rel}: missing persona_morality view (run: views)')

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
                # `question` is dropped by strip and then refilled by `items`, so unlike the other
                # instrument tables it is not required to stay empty; checked below instead.
                if name in tables and name != 'question':
                    n = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    if n:
                        failures.append(f'{rel}: {name} still holds {n} rows')

            items = con.execute('SELECT COUNT(*) FROM question').fetchone()[0] \
                if 'question' in tables else 0
            if items != expected_items:
                failures.append(f'{rel}: question holds {items} rows, expected {expected_items} '
                                f'(run: python tools/database/init_morality_dbs.py items)')

            sheets = con.execute('SELECT COUNT(*) FROM quiz_sheet').fetchone()[0] \
                if 'quiz_sheet' in tables else 0
            if sheets != 1:
                failures.append(f'{rel}: quiz_sheet holds {sheets} rows, expected 1 '
                                f'(run: python tools/database/init_morality_dbs.py items)')

            integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity != 'ok':
                failures.append(f'{rel}: integrity_check={integrity}')

            print(f'  {rel}: {personas} personas, tables={sorted(tables)}, views={sorted(views)}')
        finally:
            con.close()

    if failures:
        print('\nFAILURES:')
        for f in failures:
            print('  ' + f)
        sys.exit(1)
    print(f'\nOK: {len(morality_db_paths())} morality DBs clean')


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'all'
    sys.path.insert(0, ROOT)
    if action in ('copy', 'all'):
        print('== copy ==')
        copy_manifest()
    if action in ('strip', 'all'):
        print('== strip ==')
        strip_all()
    if action in ('views', 'all'):
        print('== views ==')
        ensure_morality_schema()
    if action in ('items', 'all'):
        print('== items ==')
        load_items()
    if action in ('verify', 'all'):
        print('== verify ==')
        verify()


if __name__ == '__main__':
    main()
