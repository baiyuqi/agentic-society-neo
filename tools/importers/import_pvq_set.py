"""Load the PVQ-21 items into the current database's question table.

Mirrors tools/importers/import_ipip_set.py, except the columns written are exactly the
ORM Question columns (id, question, options) -- the value DBs' question table is created
from the model, so it has no legacy standard_id/question_set columns.
"""

import pandas as pd


def import_pvq_set():
    from asociety.value import pvq
    from asociety.repository.experiment_rep import Question
    from asociety.repository.database import get_engine
    from sqlalchemy.orm import Session

    ids = pvq.question_ids()
    with Session(get_engine()) as session:
        existing = session.query(Question).count()
    if existing == len(ids):
        print(f"question table already holds {existing} PVQ items. Skipping import.")
        return
    if existing != 0:
        raise Exception(f"question table holds {existing} rows, expected 0 or {len(ids)}. "
                        f"Refusing to append a partial item set.")

    keyed = pvq.items()
    df = pd.DataFrame({
        'id': ids,
        'question': [keyed[q]['text'] for q in ids],
        'options': pvq.options_text(),
    })
    df.to_sql(name="question", con=get_engine(), if_exists='append', index=False)
    print(f"Imported {len(df)} PVQ items into the question table.")


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import_pvq_set()
