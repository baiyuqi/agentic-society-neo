from asociety.generator.persona_skeleton_generator import *
import json
from langchain_core.output_parsers import StrOutputParser
from asociety.generator.llm_engine import from_void

output_parser = StrOutputParser()
class PersonaGenerator:
    def __init__(self) -> None:
        from asociety.generator.llm_engine import get_llm

        self.skeletonGenerator = PersonaSkeletonGeneratorFactory.create()
        self.enricher = get_llm() | output_parser
            
    def sampling(self, n):
       
        rst = []
        for index in range(0, n):
            obj = {}
            enriched = self.enricher.invoke(from_void)
            obj["persona_desc"] = enriched;
            rst.append(obj)
        return rst


