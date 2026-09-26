"""Reorganize data/db into population/individual/work layout.

Moves the 6 population arms (renamed to semantic filenames), the individual
persona1-5 DBs, and the human baseline into the new per-instrument layout:

    data/db/<tree>/{population,individual,work}/   +   human.db

Everything else under each tree is archived to data/db/_archive/ (recoverable,
not hard-deleted, since data/db is gitignored). Run with --dry-run first.

Usage:
    python tools/database/reorganize_data_dirs.py --dry-run
    python tools/database/reorganize_data_dirs.py
"""

import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

DB_ROOT = os.path.join(ROOT, 'data', 'db')
ARCHIVE_ROOT = os.path.join(DB_ROOT, '_archive')
TREES = ('personality', 'value', 'morality')

# source (relative to <tree>/backup/) -> destination (relative to <tree>/)
POPULATION_MOVES = {
    'deepseek-chat.db': 'population/standard.db',
    'deepseek-chat-antialign.db': 'population/antialign.db',
    'deepseek-chat-narrative.db': 'population/narrative.db',
    'wiki/wiki-fiction.db': 'population/wikifiction.db',
    'thinkpersona.db': 'population/thinkpersona.db',
    'real-persona-chat.db': 'population/real-persona-chat.db',
}

# entries that must remain at the tree root after the move (everything else -> _archive)
KEEP = {'population', 'individual', 'work', 'human.db'}


def _move(src, dst):
    """Move src -> dst, creating parent dirs. No-op if dst already exists (idempotent)."""
    if not os.path.exists(src):
        return 'missing'
    if os.path.exists(dst):
        return 'exists'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return 'moved'


def plan_tree(tree, dry_run):
    """Return a list of (action, src, dst) descriptions for one tree."""
    actions = []
    tree_root = os.path.join(DB_ROOT, tree)
    backup = os.path.join(tree_root, 'backup')

    # 1. population arms (rename)
    for src_rel, dst_rel in POPULATION_MOVES.items():
        src = os.path.join(backup, *src_rel.split('/'))
        dst = os.path.join(tree_root, *dst_rel.split('/'))
        actions.append(('population', src, dst))

    # 2. individual dir
    actions.append(('individual', os.path.join(backup, 'individual'), os.path.join(tree_root, 'individual')))

    # 3. human baseline
    actions.append(('human', os.path.join(backup, 'human.db'), os.path.join(tree_root, 'human.db')))

    # 4. empty work dir
    actions.append(('workdir', None, os.path.join(tree_root, 'work')))

    # 5. archive everything else remaining at the tree root
    if os.path.isdir(tree_root):
        for name in sorted(os.listdir(tree_root)):
            if name in KEEP:
                continue
            src = os.path.join(tree_root, name)
            dst = os.path.join(ARCHIVE_ROOT, tree, name)
            actions.append(('archive', src, dst))

    return actions


def execute(actions, dry_run):
    moved = archived = missing = skipped = created = 0
    for action, src, dst in actions:
        if action == 'workdir':
            if dry_run:
                print(f'  [mkdir] {dst}')
            else:
                os.makedirs(dst, exist_ok=True)
                created += 1
            continue
        rel_src = os.path.relpath(src, ROOT) if src else ''
        rel_dst = os.path.relpath(dst, ROOT)
        if action == 'archive':
            if not os.path.exists(src):
                continue
            if dry_run:
                print(f'  [archive] {rel_src} -> {rel_dst}')
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                archived += 1
        else:
            result = _move(src, dst) if not dry_run else ('exists' if os.path.exists(dst) else ('missing' if not os.path.exists(src) else 'moved'))
            if dry_run:
                print(f'  [{action:>10}] {rel_src} -> {rel_dst}  ({result if result != "moved" else ""})')
            else:
                if result == 'moved':
                    moved += 1
                elif result == 'missing':
                    print(f'  WARN missing source: {rel_src}')
                    missing += 1
                elif result == 'exists':
                    skipped += 1
    return moved, archived, missing, skipped, created


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    for tree in TREES:
        print(f'\n== {tree} ==')
        actions = plan_tree(tree, args.dry_run)
        moved, archived, missing, skipped, created = execute(actions, args.dry_run)
        if not args.dry_run:
            print(f'   moved={moved} archived={archived} missing={missing} '
                  f'exists_skipped={skipped} workdirs={created}')

    if args.dry_run:
        print('\n(dry run — no changes made)')


if __name__ == '__main__':
    main()
