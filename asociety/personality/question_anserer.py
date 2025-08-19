from asociety.generator.persona_skeleton_generator import *
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.output_parsers import StrOutputParser
from asociety.generator.llm_engine import llm, from_skeleton
from asociety import config
with open('prompts/experiment.json', encoding='utf-8') as pjson:
            prompts = json.load(pjson)
            
           
            pjson.close()
output_parser = StrOutputParser()
question_prompt_name = config.configuration['question_prompt']
fs = prompts['ipip_neo_120'][question_prompt_name]
question_prompt = ChatPromptTemplate.from_template(fs)
chain = question_prompt | llm | output_parser
 
def getAnwser(persona, question):
        p = persona.persona_desc
        q = question.question
        o = question.options
        anwser = chain.invoke({"persona":p,"question":q, "options":o })
        
        return anwser
