"""Morality-side twin of asociety/personality/personality_analysis.py.

Everything here reads the persona_morality view (age_range + persona.* + morality.*), so the
same age/sex dimensions the personality and value curves use are available unchanged.

Column order is load-bearing: BaseCurvePanel indexes mdata[1:] positionally, so
MORALITY_TRAITS is the single source of truth for both the SELECT and the panel's
data_index_map.
"""

import numpy as np

from asociety.morality import mfq

FOUNDATIONS = list(mfq.FOUNDATION_TO_COLUMN.values())
HIGHER_ORDER = list(mfq.HIGHER_TO_COLUMN.values())
MORALITY_TRAITS = FOUNDATIONS + HIGHER_ORDER


def _engine_or(db_path):
    from sqlalchemy import create_engine
    from asociety.repository.database import get_engine
    if db_path:
        return create_engine(f'sqlite:///{db_path}')
    return get_engine()


def get_morality_ana(db_path=None, dimension='age', sex_filter='All'):
    """[dimension, <7 moral-foundation columns>] as a list of column-lists.

    The morality counterpart of personality_analysis.get_personas_ana, and the callable
    BaseCurvePanel uses as its mdata loader. The stored columns already carry the MFQ-30
    scores, so there is nothing to rescore.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    import pandas as pd

    if not dimension.isalnum() and '_' not in dimension:
        raise ValueError(f"Invalid dimension name: {dimension}")

    query = f'SELECT {dimension}, {", ".join(MORALITY_TRAITS)} FROM persona_morality'
    if sex_filter != 'All':
        if sex_filter not in ['Male', 'Female']:
            raise ValueError(f"Invalid sex filter: {sex_filter}")
        query += f" WHERE sex = '{sex_filter}'"
    query += f' ORDER BY {dimension}'

    with Session(_engine_or(db_path)) as session:
        df = pd.read_sql(text(query), session.bind)

    return [df[col].tolist() for col in df.columns]


def calculate_morality_stats(db_path=None):
    """Per-foundation mean/variance/std over the whole DB, mirroring calculate_personality_stats."""
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    import pandas as pd

    with Session(_engine_or(db_path)) as session:
        df = pd.read_sql(
            text(f'SELECT {", ".join(MORALITY_TRAITS)} FROM persona_morality'), session.bind)

    stats = {}
    for trait in MORALITY_TRAITS:
        series = pd.to_numeric(df[trait], errors='coerce').dropna()
        if series.empty:
            stats[trait] = {'mean': np.nan, 'variance': np.nan, 'std': np.nan, 'data': []}
            continue
        stats[trait] = {
            'mean': float(series.mean()),
            'variance': float(series.var()),
            'std': float(series.std()),
            'data': series.tolist(),
        }
    return stats


def project_morality_2d(method='pca'):
    """Reduce the 7-d moral vector to 2-d, returning coordinates and sex labels."""
    import pandas as pd
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    with Session(_engine_or(None)) as session:
        df = pd.read_sql(
            text(f'SELECT {", ".join(MORALITY_TRAITS)}, sex FROM persona_morality'), session.bind)
    X = df[MORALITY_TRAITS].values

    if method == 'pca':
        from sklearn.decomposition import PCA
        coords_2d = PCA(n_components=2).fit_transform(X)
    elif method == 'tsne':
        from sklearn.manifold import TSNE
        coords_2d = TSNE(n_components=2, random_state=42).fit_transform(X)
    else:
        raise ValueError('Unknown method')
    return coords_2d, df['sex'].values


def project_morality_1d():
    """Reduce the 7-d moral vector to 1-d, returning coordinates, sex labels and the df."""
    import pandas as pd
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    with Session(_engine_or(None)) as session:
        df = pd.read_sql(text('SELECT * FROM persona_morality'), session.bind)
    X = df[MORALITY_TRAITS].values

    from sklearn.decomposition import PCA
    coords_1d = PCA(n_components=1).fit_transform(X).flatten()
    return coords_1d, df['sex'].values, df
