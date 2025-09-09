from asociety.generator.persona_skeleton_generator import *
import json
from langchain_core.prompts import ChatPromptTemplate

import os

from asociety import config
model = config.configuration['llm']

if model == 'local':
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model="/data1/glm-4-9b-chat",
        api_key="aaa",
        openai_api_base="http://221.229.101.198:8000/v1"
    )
if model == 'gpt-4o':
    from langchain_openai import ChatOpenAI
    apikey = os.getenv('OPENAI_APIKEY')
    llm = ChatOpenAI(
        model="glm4-chat-9b",
        openai_api_base = "",
        api_key=apikey,
    )
if model == 'deepseek':
    from langchain_openai import ChatOpenAI
    apikey = os.getenv('DS_API_KEY')
    api_base = os.getenv('DS_BASE_URL')
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_base = api_base,
        api_key=apikey,
    )
if model == 'qwen':
    from langchain_openai import ChatOpenAI
    apikey = os.getenv('QW_API_KEY')
    api_base = os.getenv('QW_BASE_URL')
    llm = ChatOpenAI(
        model="qwen-vl-plus",
        openai_api_base=api_base,
        api_key=apikey,
    )
with open('prompts/generation.json', encoding='utf-8') as pjson:
            from asociety import config
            persona_prompt_name = config.configuration['persona_prompt']

            d = json.load(pjson)
            fs = d[persona_prompt_name]
            from_skeleton = ChatPromptTemplate.from_template(fs)
           
            fv = d["from_void"]
            from_void = ChatPromptTemplate.from_template(fv)
            big_five_explain = d["big_five_explain"]
            
            pe = d["personality_eliciting"]
            personality_eliciting = ChatPromptTemplate.from_template(pe)
            pjson.close()
with open('prompts/chat.json', encoding='utf-8') as pjson:
            d = json.load(pjson)
            sm = d["summary"]
            
            fr = d["friend"]
            friend = ChatPromptTemplate.from_template(fv)
            pjson.close()
from langchain_core.prompts import  MessagesPlaceholder
summary = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                
               
                fr,
            ),
            MessagesPlaceholder(variable_name="messages"),
            
        ]
    )