from typing import List, Dict
from generator.prompt_template import get_detect_contextual_hallucination_prompt, get_detect_consistency_hallucination_prompt
from generator.clients import openai_gpt35
from generator.output_parsers import get_JsonOutputParser, get_StrOutputParser, get_YesNoOutputParser

class ContextualDetector:
    def __init__(self, model:None, prompt=None, repeats:int=5):
        if model is None:
            model = openai_gpt35()
        if prompt is None: 
            prompt = get_detect_contextual_hallucination_prompt()
        self.repeats = repeats
        self.model = model
        self.parser = get_YesNoOutputParser()
        self.chain = prompt | model | self.parser
        self.threshold = 0.5

    def detect_one(self, transcript: str, diagnosis: str, rationale: str) -> Dict[str, float]:
        yes_votes = 0
        for _ in range(self.repeats):
            result = self.chain.invoke({"transcript": transcript, "diagnosis": diagnosis, "rationale": rationale})
            if "yes" in result.lower():
                yes_votes += 1

        score = yes_votes / self.repeats
        return {"diagnosis": diagnosis, "hallucination_score": score}

    def __call__(self, transcript: str, diag_and_rationale: List[str]) -> List[Dict[str, float]]:
        results = []
        for item in diag_and_rationale:
            diagnosis = item["diagnosis"]
            rationale = item["rationale"]
            rec = self.detect_one(transcript, diagnosis, rationale)
            rec["is_hallucinated"] = rec["hallucination_score"] >= self.threshold
            results.append(rec)
        return results
    
    
class ConsistencyDetector:
    def __init__(self, model:None, prompt=None, repeats:int=5):
        if model is None:
            model = openai_gpt35()
        if prompt is None: 
            prompt = get_detect_consistency_hallucination_prompt()
        self.repeats = repeats
        self.model = model
        self.parser = get_YesNoOutputParser()
        self.chain = prompt | model | self.parser
        self.threshold = 0.5

    def detect_one(self, transcript: str, diagnosis: str, rationale: str) -> Dict[str, float]:
        yes_votes = 0
        for _ in range(self.repeats):
            result = self.chain.invoke({"transcript": transcript, "diagnosis": diagnosis, "rationale": rationale})
            if "yes" in result.lower():
                yes_votes += 1

        score = yes_votes / self.repeats
        return {"diagnosis": diagnosis, "hallucination_score": score}

    def __call__(self, transcript: str, diag_and_rationale: List[str]) -> List[Dict[str, float]]:
        results = []
        for item in diag_and_rationale:
            diagnosis = item["diagnosis"]
            rationale = item["rationale"]
            rec = self.detect_one(transcript, diagnosis, rationale)
            rec["is_hallucinated"] = rec["hallucination_score"] >= self.threshold
            results.append(rec)
        return results
