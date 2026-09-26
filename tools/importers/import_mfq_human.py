"""Build data/db/morality/human.db, the MFQ-30 human baseline for the morality curves.

The deposit's 32 MFQ columns are renumbered onto our 30-item instrument and re-scaled onto our
0-5 scale (ours = theirs - 1), then scored by asociety.morality.mfq.compute -- the same call the
simulated personas go through. So the human curve and the simulated curves come from one
instrument and one scoring rule.

Source: the "D and Moral Foundations" deposit on OSF, node 37eht, file
dataset/d_mft_analysis_addmods.csv (N = 101,433, myPersonality-derived). Downloaded on first run
into data/MFQ/human/, whose README records the provenance and the (missing) licence. The OSF
node declares no licence, so these data are used locally for research and are not redistributed.
"""

import json
import os
import sys
import urllib.request

CSV_URL = 'https://osf.io/download/6a1fd980487f4335837df50c/'
CSV_PATH = 'data/MFQ/human/d_mft_analysis_addmods.csv'
DB_PATH = 'data/db/morality/human.db'
AGE_MEAN_PATH = 'data/cross_section/age_mean_MFQ.csv'

# Deposit column (its 1-based MFQ item number) -> our qid. MFQ_6 and MFQ_22 are the MATH/GOOD
# catch items and have no counterpart in the 30-item instrument. The map is mandatory: the
# deposit interleaves foundations (harm, fair, ingroup, respect, purity, harm, ...) while our
# data/MFQ/MFQ30.json is part-major (1-15 relevance, 16-30 agreement), so a positional zip would
# silently scramble the items. Verified three ways -- the Mplus factor loadings in
# dataset/by_country/d_mft_c*.inp, the July-2008 printed MFQ-30 key, and a text-by-text match
# against MFQ30.json (30/30 bijection).
COLUMN_TO_QID = {
    'MFQ_1': 1, 'MFQ_2': 4, 'MFQ_3': 7, 'MFQ_4': 10, 'MFQ_5': 13,
    'MFQ_7': 2, 'MFQ_8': 5, 'MFQ_9': 8,
    'MFQ_10': 11, 'MFQ_11': 14, 'MFQ_12': 3, 'MFQ_13': 6, 'MFQ_14': 9,
    'MFQ_15': 12, 'MFQ_16': 15, 'MFQ_17': 16, 'MFQ_18': 19,
    'MFQ_19': 22, 'MFQ_20': 25, 'MFQ_21': 28,
    'MFQ_23': 17, 'MFQ_24': 20, 'MFQ_25': 23, 'MFQ_26': 26,
    'MFQ_27': 29, 'MFQ_28': 18, 'MFQ_29': 21, 'MFQ_30': 24, 'MFQ_31': 27, 'MFQ_32': 30,
}

# The deposit columns in our qid order, so a row's codes line up with mfq.question_ids().
ITEM_COLUMNS = [col for col, _ in sorted(COLUMN_TO_QID.items(), key=lambda kv: kv[1])]

# The deposit codes are 1..6; our instrument is 0..5. MFQ has no within-person centring, so this
# is a pure level shift (unlike the ESS/PVQ case, where a reversal sits under a centring).
SCALE_SHIFT = 1

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
    """The respondents with all 30 items answered 1..6, sex coded, and a usable age."""
    import pandas as pd
    download()
    df = pd.read_csv(CSV_PATH, usecols=['id', 'age', 'sex'] + ITEM_COLUMNS)
    for col in ITEM_COLUMNS:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors='coerce')
    df['age'] = pd.to_numeric(df['age'], errors='coerce')

    total = len(df)
    df = df.dropna(subset=ITEM_COLUMNS, how='any')
    dropped_items = total - len(df)
    df = df[df[ITEM_COLUMNS].isin(range(1, 7)).all(axis=1)]
    dropped_codes = total - dropped_items - len(df)
    df = df[df['sex'].isin([0, 1])]
    dropped_sex = total - dropped_items - dropped_codes - len(df)
    df = df[(df['age'] >= MIN_AGE) & (df['age'] <= MAX_AGE)]
    dropped_age = total - dropped_items - dropped_codes - dropped_sex - len(df)
    print(f'{total} respondents: dropped {dropped_items} with a missing item, '
          f'{dropped_codes} with an out-of-range code, {dropped_sex} with no sex, '
          f'{dropped_age} outside {MIN_AGE}..{MAX_AGE}; {len(df)} kept.')
    return df


def score(raw):
    """The 30 deposit codes, in our qid order, as a scored result."""
    from asociety.morality import mfq
    answers = [{'id_question': qid, 'id_select': int(code) - SCALE_SHIFT}
               for qid, code in zip(mfq.question_ids(), raw)]
    return mfq.compute(answers)


def build():
    import pandas as pd
    from sqlalchemy.orm import Session

    from asociety.repository.database import get_engine, set_currentdb
    from asociety.repository.persona_rep import Persona
    from asociety.repository.moral_rep import Morality, PERSONA_MORALITY_VIEW, saveMorality
    from asociety.morality import mfq

    df = load()
    set_currentdb(DB_PATH)
    engine = get_engine()

    for path in (DB_PATH, DB_PATH + '-wal', DB_PATH + '-shm'):
        if os.path.exists(path):
            os.remove(path)
    Persona.__table__.create(engine)
    Morality.__table__.create(engine)

    personas, morals = [], []
    for i, row in enumerate(df.itertuples(index=False), start=1):
        age = int(row.age)
        # The deposit codes sex 0/1 but ships no codebook, so the direction is assumed. It is not
        # load-bearing: the morality curves read dimension='age', sex_filter='All'.
        sex = 'Male' if int(row.sex) == 1 else 'Female'
        personas.append(Persona(id=i, sourcePersonaId=f'{int(row.id)}', age=age, sex=sex))

        result = score([getattr(row, col) for col in ITEM_COLUMNS])
        m = Morality(persona_id=i, model='D-MFT', theory='moral_foundations',
                     question=len(mfq.question_ids()), morality_json=json.dumps(result))
        for name, column in mfq.FOUNDATION_TO_COLUMN.items():
            setattr(m, column, result['foundations'].get(name))
        for name, column in mfq.HIGHER_TO_COLUMN.items():
            setattr(m, column, result['higher_order'].get(name))
        morals.append(m)

    with Session(engine) as session:
        session.add_all(personas)
        session.commit()
    saveMorality(morals)

    with engine.begin() as conn:
        conn.exec_driver_sql(PERSONA_MORALITY_VIEW)
    print(f'{len(personas)} personas and morality rows written to {DB_PATH}.')

    return pd.read_sql('SELECT age_range, COUNT(*) AS sample_size, '
                       + ', '.join(f'AVG({c}) AS {c}' for c in
                                   list(mfq.FOUNDATION_TO_COLUMN.values())
                                   + list(mfq.HIGHER_TO_COLUMN.values()))
                       + ' FROM persona_morality GROUP BY age_range', engine)


def write_age_means(summary):
    """The morality analogue of data/cross_section/age_mean_ESS.csv, from the built view so the
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
