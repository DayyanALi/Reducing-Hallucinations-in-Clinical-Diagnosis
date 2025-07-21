import json
from random import choice
from typing import Any, Dict, List, Optional
from generator.clients import get_openai_gpt4
from generator.output_parsers import get_StrOutputParser
from generator.prompt_template import get_inject_contextual_hallucination_prompt, get_inject_consistency_hallucination_prompt
from utils.utils import load_json


class ContextualHallucinationInjector:
    def __init__(self, model: Any, parser = None, prompt_template: Optional[str] = None):
        self.prompt = get_inject_contextual_hallucination_prompt(parser=parser, template=prompt_template)
        self.parser = get_StrOutputParser()
        self.chain = self.prompt | model | self.parser

    def inject(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        diagnoses = record.get("diagnoses") or record.get("diag_and_rationale", [])
        if not diagnoses:
            return None

        choice_pair = choice(diagnoses)
        orig_diag = choice_pair["diagnosis"]
        orig_rat  = choice_pair["rationale"]

        transcript = record.get("transcript") or record.get("src") or record.get("dialogue") or ""

        hallucinated = self.chain.invoke({
            "transcript": transcript,
            "original_diagnosis": orig_diag,
            "original_rationale": orig_rat
        }).strip()

        if not hallucinated.endswith("."):
            hallucinated += "."

        new_rec = dict(record)  
        new_rec.update({
            "original_diagnosis": orig_diag,
            "original_rationale": orig_rat,
            "hallucinated_rationale": hallucinated,
            "error_type": "contextual_hallucination"
        })
        return new_rec


class ConsistencyHallucinationInjector:
    def __init__(self, model: Any, parser = None, prompt_template: Optional[str] = None):
        self.prompt = get_inject_consistency_hallucination_prompt(parser=parser, template=prompt_template)
        self.parser = get_StrOutputParser()
        self.chain = self.prompt | model | self.parser
        
    def inject(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        diagnoses = record.get("diagnoses") or record.get("diag_and_rationale",[])
        if not diagnoses:
            return None
        choice_pair = choice(diagnoses)
        orig_diag = choice_pair["diagnosis"]
        orig_rat = choice_pair["rationale"]
        transcript = record.get("transcript") or record.get("src") or record.get("dialogue") or ""

        hallucinated = self.chain.invoke({
            "transcript" : transcript,
            "original_diagnosis" : orig_diag,
            "original_rationale" : orig_rat,
        })

        if not hallucinated.endswith("."):
            hallucinated += "."

        new_rec = dict(record)
        new_rec.update({
            "original_diagnosis" : orig_diag,
            "original_rationale" : orig_rat,
            "hallucinated_rationale" : hallucinated,
            "error_type" : "consistency_hallucination",
        })
        return new_rec