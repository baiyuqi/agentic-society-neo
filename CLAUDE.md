# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic Society Neo is a research-focused Python project for generating AI personas with measurable personality traits. The system combines census data, LLM generation, and IPIP-NEO personality assessment to create psychologically plausible AI characters for social simulations.

## Research Focus Areas

- **Personality Identifiability**: Analyzing whether LLMs generate distinct personality profiles from different personas
- **Personality Stability**: Measuring consistency of personality traits across multiple generations
- **Statistical Validation**: Using multivariate analysis (PCA, Mahalanobis distance, clustering) to validate results

## Key Components

- **Persona Generation**: Creates AI personas from census data using LLMs (`asociety/generator/`)
- **Personality Assessment**: IPIP-NEO personality trait analysis (`asociety/personality/ipipneo/`)
- **Statistical Analysis**: Multivariate analysis tools for personality validation (`doc/` analysis documents)
- **Database Management**: SQLite database for storing personas and experiments (`asociety/repository/`)
- **Configuration**: Per-DB `meta` table (LLM, prompts, method) loaded by `config.load_from_db`

### Database Trees

`data/db/` holds one subtree per instrument, with mirrored layouts so a path maps across by
swapping one segment:

- `data/db/personality/` — the Big Five / IPIP-NEO experiment (all DBs, `backup/` included)
- `data/db/value/` — the Schwartz PVQ-21 experiment (personas + the question set at rest; the
  pipeline fills in the answers and the scores)
- `data/db/morality/` — the MFQ-30 moral-foundations experiment, built the same way: personas +
  the 30 `question` items at rest, copied from the personality tree

There is no `config.json`. Every experiment setting — including which LLM — lives in each DB's
`meta` key/value table (`llm`, `request_method`, `question_prompt`, `persona_prompt`, `model`), and
`asociety.config.load_from_db(db_path)` populates the pipeline's `config.configuration` dict from it
at the start of any entry point. The `instrument` is *not* stored: it is derived from the
`question` table count (120 → `ipip_neo_120`, 21 → `pvq_21`, 30 → `mfq_30`), falling back to the
path's tree for a brand-new DB. `verify_db_path(db_path)` wraps `load_from_db` and rejects a DB
whose path does not sit under its derived instrument's tree (the old `check_instrument_tree`
contract); every single-DB pipeline driver calls it. `studio/config_panel.py` is a DB selector +
`meta` editor (`set_meta`) that applies the same tree rule when a database is picked or saved; a
database that does not exist *yet* under the right tree is still allowed, since that is how a new
run starts. The instrument also picks the sheet policy from `asociety.config.INSTRUMENTS`:
IPIP-NEO-120 splits into 6 sheets of 20, PVQ-21 and MFQ-30 go out as a single sheet. `model` lives
in `meta`, not as a column on the results tables.

`tools/database/init_value_dbs.py all` builds the value tree and
`tools/database/init_morality_dbs.py all` the morality tree: copy, strip, schema, load the 21 PVQ /
30 MFQ items into every `question` table, verify. Both are re-runnable; `init_morality_dbs.py`
deliberately exposes no `split` action, since `data/db/` is already split into the three trees.

Each tree's `backup/human.db` is the human reference the curve panels plot against, and is *not*
a pipeline DB. The value one is built by `tools/importers/import_ess_human.py` from the ESS
PVQ-21 microdata, downloaded on its first run — see `data/ESS/README.md` for the source and the
scale-direction caveat. The morality one is built by `tools/importers/import_mfq_human.py` from
the MFQ-30 `d_mft_analysis_addmods.csv` deposit (OSF node `37eht`), whose items are interleaved
and renumbered relative to ours — see `data/MFQ/human/README.md` for the item map, the
`ours = theirs - 1` shift, and the no-licence caveat. Both are gitignored. A tree with no usable
human sample would set `human_db_path = None`; all three now have one. `doc/human_baselines_zh.md`
consolidates all three sources — including the personality branch's separate BHPS/GSOEP aggregate
reference — with the open provenance gaps (the personality `human.db` source is unrecorded).

## Development Commands

### Package Management (Poetry)
```bash
poetry install  # Install dependencies
poetry shell    # Activate virtual environment
poetry add <package>  # Add new dependency
```

Poetry is optional and is *not* installed in the environment this repo is developed in. Every
entry-point script under `tools/` (and `value_pipeline.py`) inserts the repo root into `sys.path`
itself, so from the repo root plain `python tools/…/script.py` works — and is what the READMEs
document. A script under `tools/` that imports `asociety.*` **must** carry that bootstrap, or
script-form invocation dies with `ModuleNotFoundError: No module named 'asociety'`.

### Running Tests
```bash
# Run specific test files
python -m pytest asociety/generator/llm_engine_test.py
python asociety/personality/ipipneo/test.py
```

### Database Operations
```bash
# Check database connection
python -c "from asociety.repository.database import get_engine; print(get_engine())"

# Generate personas
python -c "from asociety.generator.persona_manager import enrich_unprocessed_personas; enrich_unprocessed_personas()"
```

### Statistical Analysis
```bash
# Run personality analysis scripts
python asociety/personality/compare_personalities.py  # Identifiability analysis
python asociety/personality/personality_distribute.py  # Stability analysis (Euclidean)
python asociety/personality/personality_mahalanobis.py  # Stability analysis (Mahalanobis)
```

### Configuration
Settings live in each DB's `meta` table. Edit them through the studio's config panel, or directly:
```python
from asociety.repository.database import set_currentdb, create_tables
from asociety.repository.meta_rep import set_meta
set_currentdb('data/db/value/backup/deepseek-chat.db')
create_tables()
set_meta({'llm': 'deepseek', 'request_method': 'sheet', 'question_prompt': 'sheet_prompt'})
```
The keys are `llm`, `request_method`, `question_prompt`, `persona_prompt`, `model`; `instrument` is
derived from the `question` count. `tools/database/backfill_meta.py` (re)writes this table across
the whole tree and `verify` asserts the post-backfill invariants.

## Research Methodology

### Identifiability Analysis
- **Objective**: Determine if LLMs generate distinguishable personality profiles
- **Methods**: T-tests, PCA visualization, Mahalanobis distance, unsupervised clustering
- **Implementation**: `asociety/personality/compare_personalities.py`

### Stability Analysis  
- **Objective**: Measure personality consistency across multiple generations
- **Methods**: Euclidean distance distribution, Mahalanobis distance, PCA
- **Implementation**: `asociety/personality/personality_distribute.py`, `personality_mahalanobis.py`

## Architecture Notes

- Uses SQLAlchemy ORM for database operations
- LangChain for LLM integration
- Modular structure with separate generators, repositories, and personality modules
- Census data-driven persona generation from `data/census.csv`
- IPIP-NEO personality assessment integration
- Statistical validation framework for research rigor

## Common Development Tasks

1. **Run research analyses**: Use analysis scripts in `asociety/personality/` with datasets from `data/db/personality/backup/`
2. **Add new persona attributes**: Modify database schema in `asociety/repository/`
3. **Change LLM provider**: Update the DB's `meta.llm` and the mapping in `asociety/generator/llm_engine.py`
4. **Extend statistical methods**: Add new analysis techniques to personality modules
5. **Process experimental data**: Use repository classes to query and analyze large persona datasets

## Documentation References

- `doc/identifiability_analysis_en.md`: Detailed methodology for personality distinguishability
- `doc/stability_analysis_en.md`: Methods for measuring personality consistency
- `doc/references.md`: Academic references for LLM social simulations