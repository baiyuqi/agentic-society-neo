from asociety.generator.persona_skeleton_generator import *
import json
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from asociety import config

# generation.json is a static file, read once at import. Only `from_skeleton` depends on a config
# key (`persona_prompt`), so it is built lazily; the rest are fixed-key and stay import-time.
with open('prompts/generation.json', encoding='utf-8') as pjson:
    _GENERATION = json.load(pjson)

from_void = ChatPromptTemplate.from_template(_GENERATION["from_void"])
big_five_explain = _GENERATION["big_five_explain"]
personality_eliciting = ChatPromptTemplate.from_template(_GENERATION["personality_eliciting"])

with open('prompts/chat.json', encoding='utf-8') as pjson:
    _CHAT = json.load(pjson)

fr = _CHAT["friend"]
summary = ChatPromptTemplate.from_messages(
    [("system", fr), MessagesPlaceholder(variable_name="messages")]
)

_llm = None


def get_llm():
    """The LLM for the current DB's meta['llm'], built on first use and cached."""
    global _llm
    if _llm is not None:
        return _llm
    from langchain_openai import ChatOpenAI

    model = config.configuration['llm']
    if model == 'local':
        _llm = ChatOpenAI(
            model="/data1/glm-4-9b-chat", api_key="aaa",
            openai_api_base="http://221.229.101.198:8000/v1")
    elif model == 'gpt-4o':
        _llm = ChatOpenAI(
            model="glm4-chat-9b", openai_api_base="", api_key=os.getenv('OPENAI_APIKEY'))
    elif model == 'deepseek':
        _llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_base=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
            api_key=os.getenv('DEEPSEEK_API_KEY'))
    elif model == 'qwen':
        _llm = ChatOpenAI(
            model="qwen-vl-plus", openai_api_base=os.getenv('QW_BASE_URL'),
            api_key=os.getenv('QW_API_KEY'))
    else:
        raise ValueError(f"Unknown llm {model!r}")
    return _llm


_from_skeleton = None


def generation_templates():
    """`from_skeleton`, resolved against meta['persona_prompt'] on first use."""
    global _from_skeleton
    if _from_skeleton is None:
        _from_skeleton = ChatPromptTemplate.from_template(
            _GENERATION[config.configuration['persona_prompt']])
    return _from_skeleton


def __getattr__(name):
    # `from llm_engine import llm, from_skeleton` is used by several modules; serve them lazily so
    # the module stays importable before load_from_db has populated config.
    if name == 'llm':
        return get_llm()
    if name == 'from_skeleton':
        return generation_templates()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
