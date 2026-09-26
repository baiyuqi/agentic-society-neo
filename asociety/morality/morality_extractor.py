import json

from asociety.repository.database import get_engine
from asociety.repository.persona_rep import Persona
from asociety.morality import mfq


def morality_of(pid):
    from sqlalchemy.orm import Session
    from asociety.personality.answer_extractor import get_answers
    from asociety.repository.moral_rep import Morality

    with Session(get_engine()) as session:
        persona = session.get(Persona, pid)

    result = mfq.compute(get_answers(pid))

    m = Morality()
    m.persona_id = persona.id
    m.theory = 'moral_foundations'
    m.question = len(mfq.question_ids())
    m.morality_json = json.dumps(result)

    for name, column in mfq.FOUNDATION_TO_COLUMN.items():
        setattr(m, column, result['foundations'].get(name))
    for name, column in mfq.HIGHER_TO_COLUMN.items():
        setattr(m, column, result['higher_order'].get(name))

    return m


def extract():
    from sqlalchemy.orm import Session
    from tqdm import tqdm

    with Session(get_engine()) as session:
        ps = session.query(Persona.id).all()

    morals = []
    for persona in tqdm(ps, desc="Extracting moral foundations"):
        pid = persona[0]
        try:
            morals.append(morality_of(pid))
        except Exception as e:
            print(f"Error extracting moral foundations for persona_id {pid}: {e}")
    return morals


if __name__ == "__main__":
    from asociety.repository.moral_rep import saveMorality
    saveMorality(extract())
