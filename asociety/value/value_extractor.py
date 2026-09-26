import json

from asociety.repository.database import get_engine
from asociety.repository.persona_rep import Persona
from asociety.value import pvq


def value_of(pid):
    from sqlalchemy.orm import Session
    from asociety.personality.answer_extractor import get_answers
    from asociety.repository.value_rep import Value

    with Session(get_engine()) as session:
        persona = session.get(Persona, pid)

    result = pvq.compute(get_answers(pid))

    v = Value()
    v.persona_id = persona.id
    v.theory = 'schwartz'
    v.question = len(pvq.question_ids())
    v.value_json = json.dumps(result)

    for name, column in pvq.VALUE_TO_COLUMN.items():
        setattr(v, column, result['values'].get(name))
    for name, column in pvq.HIGHER_TO_COLUMN.items():
        setattr(v, column, result['higher_order'].get(name))

    return v


def extract():
    from sqlalchemy.orm import Session
    from tqdm import tqdm

    with Session(get_engine()) as session:
        ps = session.query(Persona.id).all()

    values = []
    for persona in tqdm(ps, desc="Extracting values"):
        pid = persona[0]
        try:
            values.append(value_of(pid))
        except Exception as e:
            print(f"Error extracting values for persona_id {pid}: {e}")
    return values


if __name__ == "__main__":
    from asociety.repository.value_rep import saveValues
    saveValues(extract())
