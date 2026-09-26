"""Build data/db/value/human.db, the ESS human baseline for the value curves.

The ESS item codes are reversed onto the PVQ-21 scale (ours = 7 - ess; the ESS response scale
runs the other way, 1 = "Very much like me") and then scored by asociety.value.pvq.compute --
the same call the simulated personas go through. So the human curve and the simulated curves
come from one instrument and one scoring rule, with no subset or rescoring relation between
them.

Source: ESS Round 11, four countries (PT / ES / FR / UK), released as "ESS11_4countries_values",
DOI 10.5281/zenodo.18401503 (CC BY 4.0). Downloaded on first run into data/ESS/, whose README
records the provenance; data/ESS/sintax_values.sps is the official ESS scoring syntax this
module mirrors.
"""

import json
import os
import sys
import urllib.request

CSV_URL = ('https://zenodo.org/api/records/18401503/files/'
           'ESS11_4countries_values.csv/content')
CSV_PATH = 'data/ESS/ESS11_4countries_values.csv'
DB_PATH = 'data/db/value/human.db'
AGE_MEAN_PATH = 'data/cross_section/age_mean_ESS.csv'

# The 21 ESS item columns in questionnaire order, which is the order of pvq ids 1..21. ESS
# releases the ascending-rotation item variables with a trailing 'a' (ipcrtiva is the variable
# sintax_values.sps calls ipcrtiv).
ITEM_VARS = [
    'ipcrtiva', 'impricha', 'ipeqopta', 'ipshabta', 'impsafea', 'impdiffa', 'ipfrulea',
    'ipudrsta', 'ipmodsta', 'ipgdtima', 'impfreea', 'iphlppla', 'ipsucesa', 'ipstrgva',
    'ipadvnta', 'ipbhprpa', 'iprspota', 'iplylfra', 'impenva', 'imptrada', 'impfuna',
]

# ESS codes 1 = "Very much like me" .. 6 = "Not like me at all"; our scale runs the other way.
REVERSE_BASE = 7

MIN_AGE, MAX_AGE = 16, 110


def download(path=CSV_PATH):
    if os.path.exists(path):
        print(f'{path} already present.')
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f'Downloading {CSV_URL} ...')
    urllib.request.urlretrieve(CSV_URL, path)
    print(f'Saved {os.path.getsize(path)} bytes to {path}.')


def load():
    """The respondents with all 21 items answered 1..6 and a usable age."""
    import pandas as pd
    download()
    df = pd.read_csv(CSV_PATH, usecols=['idno', 'Country_r', 'gndr', 'agea'] + ITEM_VARS)
    for var in ITEM_VARS:
        df[var] = pd.to_numeric(df[var].astype(str).str.strip(), errors='coerce')
    df['agea'] = pd.to_numeric(df['agea'], errors='coerce')

    total = len(df)
    df = df.dropna(subset=ITEM_VARS, how='any')
    dropped_items = total - len(df)
    df = df[df[ITEM_VARS].isin(range(1, 7)).all(axis=1)]
    dropped_codes = total - dropped_items - len(df)
    df = df[df['gndr'].isin([1, 2])]
    dropped_sex = total - dropped_items - dropped_codes - len(df)
    df = df[(df['agea'] >= MIN_AGE) & (df['agea'] <= MAX_AGE)]
    dropped_age = total - dropped_items - dropped_codes - dropped_sex - len(df)
    print(f'{total} respondents: dropped {dropped_items} with a missing item, '
          f'{dropped_codes} with an out-of-range code, {dropped_sex} with no sex, '
          f'{dropped_age} outside {MIN_AGE}..{MAX_AGE}; {len(df)} kept.')
    return df


def score(raw):
    """The 21 ESS codes, in ESS questionnaire order (= pvq id order), as a scored result."""
    from asociety.value import pvq
    answers = [{'id_question': qid, 'id_select': REVERSE_BASE - int(code)}
               for qid, code in zip(pvq.question_ids(), raw)]
    return pvq.compute(answers)


def build():
    import pandas as pd
    from sqlalchemy.orm import Session

    from asociety.repository.database import get_engine, set_currentdb
    from asociety.repository.persona_rep import Persona
    from asociety.repository.value_rep import Value, PERSONA_VALUE_VIEW, saveValues
    from asociety.value import pvq

    df = load()
    set_currentdb(DB_PATH)
    engine = get_engine()

    for path in (DB_PATH, DB_PATH + '-wal', DB_PATH + '-shm'):
        if os.path.exists(path):
            os.remove(path)
    Persona.__table__.create(engine)
    Value.__table__.create(engine)

    personas, values = [], []
    for i, row in enumerate(df.itertuples(index=False), start=1):
        age = int(row.agea)
        sex = 'Male' if int(row.gndr) == 1 else 'Female'
        personas.append(Persona(id=i, sourcePersonaId=f'{int(row.Country_r)}-{int(row.idno)}',
                                age=age, sex=sex))

        result = score([getattr(row, var) for var in ITEM_VARS])
        v = Value(persona_id=i, model='ESS11', theory='schwartz',
                  question=len(pvq.question_ids()), value_json=json.dumps(result))
        for name, column in pvq.VALUE_TO_COLUMN.items():
            setattr(v, column, result['values'].get(name))
        for name, column in pvq.HIGHER_TO_COLUMN.items():
            setattr(v, column, result['higher_order'].get(name))
        values.append(v)

    with Session(engine) as session:
        session.add_all(personas)
        session.commit()
    saveValues(values)

    with engine.begin() as conn:
        conn.exec_driver_sql(PERSONA_VALUE_VIEW)
    print(f'{len(personas)} personas and value rows written to {DB_PATH}.')

    return pd.read_sql('SELECT age_range, COUNT(*) AS sample_size, '
                       + ', '.join(f'AVG({c}) AS {c}' for c in
                                   list(pvq.VALUE_TO_COLUMN.values())
                                   + list(pvq.HIGHER_TO_COLUMN.values()))
                       + ' FROM persona_value GROUP BY age_range', engine)


def write_age_means(summary):
    """The values analogue of data/cross_section/age_mean_BHPS.csv, from the built view so the
    age buckets are by construction the same ones the panels use."""
    summary = summary.copy()
    summary['_order'] = summary['age_range'].str.split('_').str[0].astype(int)
    summary = summary.sort_values('_order').drop(columns='_order')
    os.makedirs(os.path.dirname(AGE_MEAN_PATH), exist_ok=True)
    summary.to_csv(AGE_MEAN_PATH, index=False, float_format='%.4f')
    print(f'{len(summary)} age bands written to {AGE_MEAN_PATH}.')


def main():
    write_age_means(build())


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    main()
