from asociety.repository.experiment_rep import QuizAnswer
from asociety.repository.persona_rep import Persona
from asociety.repository.experiment_rep import QuestionAnswer
from asociety.repository.database import get_engine
def get_answers(persona_id):
    from asociety.config import configuration
    try:
        if configuration['request_method'] == 'question':
            return answers_by_question(persona_id)
        else:
            return answers_by_quiz(persona_id)
    except Exception as e:
        print(f"Error getting answers for persona_id {persona_id}: {e}")
        return []
def answers_by_question(persona_id):
    from sqlalchemy.orm import Session
    with Session(get_engine()) as session:
        qas = session.query(QuestionAnswer).filter(QuestionAnswer.persona_id==persona_id).all()
    all = []
    for qa in qas:
        answer = __parseChoice(qa.response)
        p = {}
        p['id_question'] =  qa.question_id
        p['id_select'] = answer
        all.append(p)

    return all


def __parseChoice(text):
    if(text == None):
       print("没有获得回答，返回1")
       return 1
    import re
    pattern = r"\*\*(\d+):|\[(\d+)\]|\*\*(\d+)\*\*|\[nchoice\]: (\d+)"

    match = re.search(pattern, text)

    if match:
        # 因为用了两个捕获组，可能只匹配到其中一个
        number = next(g for g in match.groups() if g)

        return int(number)
    else:
        print("匹配失败，返回1")
        print(text)
        return 1
def answers_by_quiz(persona_id):
    from sqlalchemy.orm import Session
    with Session(get_engine()) as session:
        qas = session.query(QuizAnswer).filter(QuizAnswer.persona_id==persona_id).order_by(QuizAnswer.sheet_id).all()
    
    all_answers_raw = []
    for qa in qas:
        answer = qa.agent_answer
        import json
        try:
            # awo is a list of answer objects, e.g., [{'question_id': 115, 'answer': 4, 'rationale': '...'}]
            awo = json.loads(answer)
        except (json.JSONDecodeError, TypeError):
            import random
            print(f"JSON parsing error or invalid data for persona_id {persona_id}. Skipping answer sheet.")
            print(f"Problematic data: {answer}")
            # We cannot create fake answers here because we don't know which question IDs this sheet contained.
            # It's better to skip this sheet's data.
            continue
        if awo:
            all_answers_raw.extend(awo)

    # Directly map the raw answers to the final format, preserving the original question_id
    final_answers = []
    for p in all_answers_raw:
        # Ensure the record is a dictionary and has the required keys
        if isinstance(p, dict) and 'question_id' in p and 'answer' in p:
            final_answers.append({
                'id_question': p['question_id'],
                'id_select': p['answer']
            })
        else:
            print(f"Skipping malformed answer record for persona_id {persona_id}: {p}")

    return final_answers
