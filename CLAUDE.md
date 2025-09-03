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
- **Configuration**: Central config via `config.json` with LLM and database settings

## Development Commands

### Package Management (Poetry)
```bash
poetry install  # Install dependencies
poetry shell    # Activate virtual environment
poetry add <package>  # Add new dependency
```

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
Edit `config.json` to change:
- LLM provider (`deepseek`)
- Database path
- Prompt templates
- Request methods

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

1. **Run research analyses**: Use analysis scripts in `asociety/personality/` with datasets from `data/db/backup/`
2. **Add new persona attributes**: Modify database schema in `asociety/repository/`
3. **Change LLM provider**: Update `config.json` and LLM engine in `asociety/generator/llm_engine.py`
4. **Extend statistical methods**: Add new analysis techniques to personality modules
5. **Process experimental data**: Use repository classes to query and analyze large persona datasets

## Documentation References

- `doc/identifiability_analysis_en.md`: Detailed methodology for personality distinguishability
- `doc/stability_analysis_en.md`: Methods for measuring personality consistency
- `doc/references.md`: Academic references for LLM social simulations