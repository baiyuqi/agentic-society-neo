from langchain_core.prompts import ChatPromptTemplate
import json
from langchain_core.output_parsers import StrOutputParser
from asociety.generator.llm_engine import llm, from_skeleton
from asociety.repository.database import get_engine

from sqlalchemy.orm import Session
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

with open('prompts/experiment.json', encoding='utf-8') as pjson:
            from asociety import config
            persona_prompt_name = config.configuration['question_prompt']
            prompts = json.load(pjson)
            qprompt = prompts['ipip_neo_120'][persona_prompt_name]
            
           
            pjson.close()
output_parser = StrOutputParser()

def update_task(record):
        

    from sqlalchemy.orm import Session
    from asociety.repository.experiment_rep import QuizAnswer
    
    from sqlalchemy import select
    with Session(get_engine()) as session:
        qa =  session.execute(select(QuizAnswer).filter_by(sheet_id = record['sheet_id'], persona_id =record['persona_id'])).scalar_one()
        if 'agent_answer' in record:
            qa.agent_answer = record['agent_answer']
        qa.response = record['response']
        session.commit()
        
def getAnwser(persona,sheet):
     

        question_prompt = ChatPromptTemplate.from_template(qprompt)
        #pro = question_prompt.invoke({"persona":persona,"sheet":sheet})
        chain = question_prompt | llm | output_parser
        if(persona == None or persona == '' ):
             anwser = chain.invoke({"sheet":sheet})
        else:
            anwser = chain.invoke({"persona":persona,"sheet":sheet})
        
        return anwser
def parse(response):
        import re
        rs = re.findall(r"\{(.*?)\}",response,re.DOTALL)
        rs = ['{' + e + '}' for e in rs]
        if(len(rs) == 0):
            print(rs)
        jsons = ','.join(rs)
        jsons = '[' + jsons + ']'
       
        return jsons

def process_row(row_info, sheet_dict, persona_dict):
    try:
        i, row = row_info
        persona_id = int(row['persona_id'])
        persona = persona_dict[persona_id]
        sheet_id = int(row['sheet_id'])
        sheet = sheet_dict[sheet_id]
        resp = getAnwser(persona.persona_desc, sheet)
        awnser = parse(resp)
        rec = {'sheet_id': sheet_id, 'persona_id': persona_id, 'response': resp, 'agent_answer': awnser}
        update_task(rec)
        return f"Task for persona {persona_id} and sheet {sheet_id} completed."
    except Exception as e:
        print(f"Error processing persona {persona_id} and sheet {sheet_id}: {e}")
        return f"Error processing persona {persona_id} and sheet {sheet_id}: {e}"

def execute_tasks():
    from asociety.repository.experiment_rep import QuizSheet
    from asociety.repository.persona_rep import Persona
    with Session(get_engine()) as session:
        sheets = session.query(QuizSheet).all()
        sheet_dict = {sheet.id: sheet.sheet for sheet in sheets}
        
        personas = session.query(Persona).all()
        persona_dict = {p.id: p for p in personas}

    sql = "SELECT * from quiz_answer where  agent_answer IS NULL "
    df = pd.read_sql_query(sql, get_engine())

    with ThreadPoolExecutor(max_workers=15) as executor:
        # Use a lambda to pass sheet_dict and persona_dict to process_row
        results = list(tqdm(executor.map(lambda item: process_row(item, sheet_dict, persona_dict), df.iterrows()), total=len(df), desc="Executing tasks"))

    for result in results:
        print(result)

def create_tasks():
    from asociety.repository.database import get_engine
    from asociety.repository.persona_rep import Persona
    from asociety.repository.experiment_rep import QuizAnswer

    with Session(get_engine()) as session:
        persona_count = session.query(Persona).count()
        answer_count = session.query(QuizAnswer).count()
        expected_count = persona_count * 6

        if answer_count == expected_count:
            print(f"quiz_answer table is already populated with {answer_count} records. Skipping task creation.")
            return
        
        if answer_count != 0:
            raise Exception(f"quiz_answer table is in an inconsistent state. "
                            f"Expected {expected_count} or 0 records, but found {answer_count}.")

        # 获取 persona_id 列表
        pids = session.query(Persona.id).all()
        # pids 是 [(1,), (2,), ...]，需要扁平化
        pdf = pd.DataFrame([pid[0] for pid in pids], columns=['persona_id'])

        # 假设 sheet_id 是 1,2,3,4,5,6
        sdf = pd.DataFrame([1, 2, 3, 4, 5, 6], columns=['sheet_id'])

        # 笛卡尔积
        pdf['key'] = 1
        sdf['key'] = 1
        qas = pd.merge(pdf, sdf, on='key').drop('key', axis=1)

        # 存到数据库表 quiz_answer
        qas.to_sql('quiz_answer', con=session.get_bind(), if_exists='append', index=False)

        session.commit()
        print("保存成功，共写入", len(qas), "条记录")

    
def create_sheets():
    from asociety.repository.database import get_engine
    from asociety.repository.experiment_rep import Question, QuizSheet
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    import numpy as np
    import json

    engine = get_engine()
    with Session(engine) as session:
        # 1️⃣ 清空 quiz_sheet 表并重置自增 ID
        try:
            # 使用 ORM 对象删除所有记录
            session.query(QuizSheet).delete(synchronize_session=False)
            
            # 重置 SQLite 的自增序列
            # 注意：这特定于 SQLite
            session.execute(text("DELETE FROM sqlite_sequence WHERE name='quiz_sheet'"))
            
            session.commit()
            print("Table 'quiz_sheet' has been cleared and its auto-increment counter has been reset.")
        except Exception as e:
            session.rollback()
            print(f"An error occurred while clearing the table: {e}")
            return

        # 2️⃣ 查询所有问题 id
        qids = session.query(Question.id).all()
        qids = [qid[0] for qid in qids]  # 转成纯 id 列表
        length = len(qids)

        if length == 0:
            print("No questions found in the 'question' table. Cannot create sheets.")
            return

        # 3️⃣ 每 20 个问题分一组
        n = (length + 19) // 20 # 更简洁的计算方式

        subs = np.array_split(qids, n)

        # 4️⃣ 创建并存储新的 sheet
        for sub in subs:
            if sub.size == 0:
                continue
                
            sub_quiz_text = create_sheet(sub.tolist())
            
            sheet_obj = QuizSheet(
                sheet=sub_quiz_text # 直接存储拼接好的文本
            )
            session.add(sheet_obj)

        session.commit()
        print(f"Successfully created and saved {len(subs)} new quiz sheets.")


def create_sheet(sub):
    from asociety.repository.database import get_engine
    from asociety.repository.experiment_rep import Question
    from sqlalchemy.orm import Session

    sheet_parts = []
    with Session(get_engine()) as session:
        for qid in sub:
            q = session.get_one(Question, qid)
            # Build the question block and add it to the list
            # Using a list and join is more efficient than repeated string concatenation
            question_block = (
                f"\n\n{qid}: {q.question}\n"
                f"Following are options to choose from:\n"
                f"{q.options}"
            )
            sheet_parts.append(question_block)
            
    return "".join(sheet_parts)

from sqlalchemy.orm import Session
from sqlalchemy import text

def create_quiz_tables():
    with Session(get_engine()) as session:
        engine = session.get_bind()

        with engine.connect() as conn:  # 显式获取 Connection
            create_quiz_sheet_sql = """
            CREATE TABLE IF NOT EXISTS quiz_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sheet TEXT
            );
            """

            create_quiz_answer_sql = """
           CREATE TABLE IF NOT EXISTS quiz_answer (
                sheet_id VARCHAR(30),
                persona_id VARCHAR(30),
                agent_answer TEXT,
                response TEXT,
                PRIMARY KEY (sheet_id, persona_id)
            );

            """

            #conn.execute(text(create_quiz_sheet_sql))
            conn.execute(text(create_quiz_answer_sql))

        session.commit()
        print("quiz_sheet 和 quiz_answer 表已创建（如果原来没有的话）")

if __name__ == "__main__":
    create_sheets()