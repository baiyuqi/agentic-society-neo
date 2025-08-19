
from sqlalchemy.orm import Session
from asociety.repository.database import get_engine
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
pool = ThreadPoolExecutor(max_workers = 10)
from asociety.repository.experiment_rep import Question, QuestionAnswer
def initializeQuestionAnswer():
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from tqdm import tqdm
    with Session(get_engine()) as session:
        ps = session.query(Persona.id).all()
        qs = session.query(Question.id).all()
        for p in tqdm(ps, desc='Initializing question_answer for personas'):
            p = p[0]
            for q in qs:
                q = q[0]
                # 只在不存在时插入
                exists_qa = session.query(session.query(QuestionAnswer).filter(QuestionAnswer.persona_id == p, QuestionAnswer.question_id == q).exists()).scalar()
                if exists_qa:
                    continue
                pq = QuestionAnswer(
                    persona_id = p,
                    question_id = q
                )
                session.add(pq)
        session.commit()
from asociety.repository.persona_rep import Persona
from asociety.personality.question_anserer import getAnwser
from tqdm import tqdm
def questionAnswerByPersona(personaId):
    from sqlalchemy.orm import Session
    qs = []
    with Session(get_engine()) as session:


        qs = session.query(QuestionAnswer.question_id).filter(QuestionAnswer.persona_id == personaId).all()

    for q in tqdm(qs, desc="Answering questions for persona:" + str(personaId)):
        q = q[0]
        qa = questionAnswer(personaId=personaId, questionId=q)
def questionAnswerAll2():
    from sqlalchemy.orm import Session
    qs = []
    with Session(get_engine()) as session:


        qs = session.query(QuestionAnswer.persona_id, QuestionAnswer.question_id).filter(QuestionAnswer.response == None).all()
    with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(questionAnswer, pq[0],pq[1]): pq for pq in qs}
            # as_completed gives us futures as they complete
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
                result = future.result()
               
  
            executor.shutdown(wait=True)
def questionAnswerAll():
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from sqlalchemy import exists
    with Session(get_engine()) as session:
        ps = session.query(Persona.id).all()

        for p in tqdm(ps, desc="Answering questions for personas"):
            p = p[0]
            pool.submit(questionAnswerByPersona,p)
            #questionAnswerByPersona(p)
    pool.shutdown(wait=True)
def questionAnswer(personaId, questionId):
    from sqlalchemy.orm import Session
    with Session(get_engine()) as session:
        qa:QuestionAnswer = session.query(QuestionAnswer).filter(QuestionAnswer.persona_id == personaId,QuestionAnswer.question_id == questionId).one();
        if(qa.response != None):
            return
        persona = session.query(Persona).filter(Persona.id == personaId).one()
        question = session.query(Question).filter(Question.id == questionId).one()

        answer = getAnwser(persona=persona, question=question)

        session.query(QuestionAnswer).filter(QuestionAnswer.persona_id == personaId,QuestionAnswer.question_id == questionId).update({QuestionAnswer.response: answer})
        session.commit()  
def parseChoice(text):
    import re


    # 使用正则表达式匹配 [数字]
    pattern = r"\[(\d+)\]"

    # 进行匹配
    match = re.search(pattern, text)

    if match:
        number = match.group(1)  # 提取匹配的数字部分
        return number
    else:
        return 1
if __name__ == "__main__":
    questionAnswerByPersona(2)
    resp = '''
Given the description of the 24-year-old Black man in the U.S., he comes across as practical, grounded, and focused on stability. While he values hard work and dedication, he doesn’t seem overly anxious or prone to excessive worry—he’s more likely to approach challenges with resilience and a solutions-oriented mindset. His confidence in his ability to build relationships and his steady progress in life suggest he doesn’t dwell on worries unnecessarily.  

That said, being married and working in sales (a field with some unpredictability) might occasionally lead to moderate concern about responsibilities or future goals. However, this wouldn’t dominate his personality.  

The most fitting response would be **2: Moderately Inaccurate**, as worry isn’t a defining trait for him, but it’s not entirely absent either.  

[2]
'''
    c = parseChoice(resp)
    print(c)

    