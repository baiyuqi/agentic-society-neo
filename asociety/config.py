import os

# Get the root directory of the project (assuming this file is in asociety/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# There is no config.json. Every experiment setting — including which LLM — lives in the current
# DB's `meta` table and is loaded into this dict by load_from_db() at the start of any pipeline
# entry point. The pipeline reads this dict, so the mechanism is unchanged; only the source moved.
configuration = {}

DEFAULT_INSTRUMENT = 'ipip_neo_120'

# Per-instrument facts the pipeline needs. `tree` is the database subtree the instrument's items
# live in: `instrument` and `database` are two independent concepts, and a mismatch between them is
# silent exactly where it matters — a scorer keeps only the question ids its own instrument
# defines, so an instrument pointed at another instrument's database would score a prefix of the
# wrong item set and write plausible-looking columns.
#
# `sheet_size` is how many items go into one quiz sheet, replacing the old `split_sheets` flag: the
# IPIP-NEO-120 is too long for a single prompt (120 -> 6 sheets of 20), while PVQ-21 and MFQ-30 are
# administered whole (None -> one sheet).
INSTRUMENTS = {
    'ipip_neo_120': {'tree': 'data/db/personality/', 'sheet_size': 20},
    'pvq_21': {'tree': 'data/db/value/', 'sheet_size': None},
    'mfq_30': {'tree': 'data/db/morality/', 'sheet_size': None},
}

_QUESTION_COUNT_TO_INSTRUMENT = {120: 'ipip_neo_120', 21: 'pvq_21', 30: 'mfq_30'}
_PATH_TO_INSTRUMENT = {spec['tree']: name for name, spec in INSTRUMENTS.items()}


def instrument_from_question_count(n):
    """The instrument a `question` table of `n` rows belongs to."""
    try:
        return _QUESTION_COUNT_TO_INSTRUMENT[int(n)]
    except (KeyError, TypeError, ValueError):
        raise ValueError(
            f"Unknown instrument for {n!r} question rows. Expected 120, 21, or 30.")


def instrument_spec(instrument=None):
    """The current instrument's entry in INSTRUMENTS."""
    if instrument is None:
        instrument = configuration.get('instrument', DEFAULT_INSTRUMENT)
    if instrument not in INSTRUMENTS:
        raise ValueError(
            f"Unknown instrument {instrument!r}. Add it to asociety.config.INSTRUMENTS with the "
            f"database tree its items live in and its sheet size.")
    return INSTRUMENTS[instrument]


def sheet_size(instrument=None):
    """Items per quiz sheet, or None when the whole item set goes in one sheet."""
    return instrument_spec(instrument)['sheet_size']


def match_instrument_tree(instrument, database):
    """Whether `database` sits in `instrument`'s tree."""
    return str(database).replace('\\', '/').startswith(instrument_spec(instrument)['tree'])


def _count_questions():
    from sqlalchemy import text
    from asociety.repository.database import get_engine
    with get_engine().begin() as conn:
        return conn.execute(text('SELECT COUNT(*) FROM question')).scalar()


def load_from_db(db_path):
    """Point the process at `db_path` and load its meta into `configuration`.

    This is the single seam that replaces config.json: call it once at the start of any pipeline
    entry point, then every module that reads `configuration` sees this DB's settings. `instrument`
    is derived from the `question` table count, not stored in meta.
    """
    from asociety.repository.database import set_currentdb, create_tables
    from asociety.repository.meta_rep import get_meta

    set_currentdb(db_path)
    create_tables()
    meta = get_meta()

    try:
        instrument = instrument_from_question_count(_count_questions())
    except ValueError:
        # A brand-new run has no question rows yet; fall back to the tree the path lives in.
        instrument = _instrument_from_path(db_path)

    configuration.update({
        'database': db_path,
        'instrument': instrument,
        'llm': meta.get('llm'),
        'request_method': meta.get('request_method'),
        'question_prompt': meta.get('question_prompt'),
        'persona_prompt': meta.get('persona_prompt'),
        'model': meta.get('model'),
    })
    return configuration


def _instrument_from_path(db_path):
    path = str(db_path).replace('\\', '/')
    for tree, name in _PATH_TO_INSTRUMENT.items():
        if path.startswith(tree):
            return name
    return None


def verify_db_path(db_path):
    """Load `db_path` and fail unless its instrument and path agree.

    Keeps the old `check_instrument_tree` contract (raise when the database does not sit under its
    instrument's tree), but derives the instrument from the DB itself rather than a config file.
    """
    load_from_db(db_path)
    instrument = configuration['instrument']
    database = str(configuration['database'])
    if not match_instrument_tree(instrument, database):
        tree = instrument_spec(instrument)['tree']
        raise ValueError(
            f"instrument {instrument!r} belongs in {tree}, but the database is {database!r}. "
            f"Set database to a DB under {tree}, or switch the instrument.")
    return database
