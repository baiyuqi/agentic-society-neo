import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

output_parser = StrOutputParser()

def _question_prompt_text():
    from asociety import config
    with open('prompts/experiment.json', encoding='utf-8') as f:
        prompts = json.load(f)
    return prompts[config.configuration['instrument']][config.configuration['question_prompt']]

def getAnwser(persona, question):
        from asociety.generator.llm_engine import get_llm
        p = persona.persona_desc
        q = question.question
        o = question.options
        question_prompt = ChatPromptTemplate.from_template(_question_prompt_text())
        chain = question_prompt | get_llm() | output_parser
        anwser = chain.invoke({"persona":p,"question":q, "options":o })

        return anwser
