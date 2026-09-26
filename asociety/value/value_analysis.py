"""Value-side twin of asociety/personality/personality_analysis.py.

Everything here reads the persona_value view (age_range + persona.* + value.*), so the
same age/sex dimensions the personality curves use are available unchanged.

Column order is load-bearing: BaseCurvePanel indexes mdata[1:] positionally, so
VALUE_TRAITS is the single source of truth for both the SELECT and the panel's
data_index_map.
"""

import numpy as np

from asociety.value import pvq

PRIMARY_VALUES = list(pvq.VALUE_TO_COLUMN.values())
HIGHER_ORDER_VALUES = list(pvq.HIGHER_TO_COLUMN.values())
VALUE_TRAITS = PRIMARY_VALUES + HIGHER_ORDER_VALUES


def _engine_or(db_path):
    from sqlalchemy import create_engine
    from asociety.repository.database import get_engine
    if db_path:
        return create_engine(f'sqlite:///{db_path}')
    return get_engine()


def get_values_ana(db_path=None, dimension='age', sex_filter='All'):
    """[dimension, <14 value columns>] as a list of column-lists.

    The value counterpart of personality_analysis.get_personas_ana, and the callable
    BaseCurvePanel uses as its mdata loader. The stored columns already carry the PVQ-21
    scores, so there is nothing to rescore.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    import pandas as pd

    if not dimension.isalnum() and '_' not in dimension:
        raise ValueError(f"Invalid dimension name: {dimension}")

    query = f'SELECT {dimension}, {", ".join(VALUE_TRAITS)} FROM persona_value'
    if sex_filter != 'All':
        if sex_filter not in ['Male', 'Female']:
            raise ValueError(f"Invalid sex filter: {sex_filter}")
        query += f" WHERE sex = '{sex_filter}'"
    query += f' ORDER BY {dimension}'

    with Session(_engine_or(db_path)) as session:
        df = pd.read_sql(text(query), session.bind)

    return [df[col].tolist() for col in df.columns]


def calculate_value_stats(db_path=None):
    """Per-value mean/variance/std over the whole DB, mirroring calculate_personality_stats."""
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    import pandas as pd

    with Session(_engine_or(db_path)) as session:
        df = pd.read_sql(
            text(f'SELECT {", ".join(VALUE_TRAITS)} FROM persona_value'), session.bind)

    stats = {}
    for trait in VALUE_TRAITS:
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


def project_values_2d(method='pca'):
    """Reduce the 14-d value vector to 2-d, returning coordinates and sex labels."""
    import pandas as pd
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    with Session(_engine_or(None)) as session:
        df = pd.read_sql(
            text(f'SELECT {", ".join(VALUE_TRAITS)}, sex FROM persona_value'), session.bind)
    X = df[VALUE_TRAITS].values

    if method == 'pca':
        from sklearn.decomposition import PCA
        coords_2d = PCA(n_components=2).fit_transform(X)
    elif method == 'tsne':
        from sklearn.manifold import TSNE
        coords_2d = TSNE(n_components=2, random_state=42).fit_transform(X)
    else:
        raise ValueError('Unknown method')
    return coords_2d, df['sex'].values


def project_values_1d():
    """Reduce the 14-d value vector to 1-d, returning coordinates, sex labels and the df."""
    import pandas as pd
    from sqlalchemy.orm import Session
    from sqlalchemy import text

    with Session(_engine_or(None)) as session:
        df = pd.read_sql(text('SELECT * FROM persona_value'), session.bind)
    X = df[VALUE_TRAITS].values

    from sklearn.decomposition import PCA
    coords_1d = PCA(n_components=1).fit_transform(X).flatten()
    return coords_1d, df['sex'].values, df
