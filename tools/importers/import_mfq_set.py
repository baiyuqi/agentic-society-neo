"""Load the MFQ-30 items into the current database's question table.

Mirrors tools/importers/import_pvq_set.py, except the options column is written per row: the MFQ
mixes two 0-5 scales (relevance, agreement), so a single shared option block would be wrong for
half the items.
"""

import pandas as pd


def import_mfq_set():
    from asociety.morality import mfq
    from asociety.repository.experiment_rep import Question
    from asociety.repository.database import get_engine
    from sqlalchemy.orm import Session

    ids = mfq.question_ids()
    with Session(get_engine()) as session:
        existing = session.query(Question).count()
    if existing == len(ids):
        print(f"question table already holds {existing} MFQ items. Skipping import.")
        return
    if existing != 0:
        raise Exception(f"question table holds {existing} rows, expected 0 or {len(ids)}. "
                        f"Refusing to append a partial item set.")

    keyed = mfq.items()
    df = pd.DataFrame({
        'id': ids,
        'question': [mfq.question_text(q) for q in ids],
        'options': [mfq.options_text(keyed[q]['part']) for q in ids],
    })
    df.to_sql(name="question", con=get_engine(), if_exists='append', index=False)
    print(f"Imported {len(df)} MFQ items into the question table.")


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import_mfq_set()
