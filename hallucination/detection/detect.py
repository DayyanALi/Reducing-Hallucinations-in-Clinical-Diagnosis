from typing import List, Dict
from generator.prompt_template import get_detect_contextual_hallucination_prompt, get_detect_consistency_hallucination_prompt, get_decompose_prompt, get_attest_prompt
from generator.clients import openai_gpt35
from generator.output_parsers import get_JsonOutputParser, get_StrOutputParser, get_YesNoOutputParser
from typing import Dict, Any
import json

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


class EntailmentDetector:
    def __init__(self, model, threshold=0.5):
        self.model = model
        self.threshold = threshold
        self.decompose_prompt = get_decompose_prompt()
        self.attest_prompt = get_attest_prompt()

    def decompose_rationale(self, rationale: str) -> List[str]:
        prompt = self.decompose_prompt.format(rationale=rationale)
        response = self.model.invoke(prompt)  # Use invoke for ChatModel

        try:
            # If using ChatModel, response is AIMessage; get content string
            response_text = response.content if hasattr(response, "content") else str(response)
            return json.loads(response_text)
        except Exception as e:
            print(f"Decomposition failed: {e}")
            return []

    def attest_claim(self, claim: str, transcript: str) -> Dict[str, str]:
        prompt = self.attest_prompt.format(claim=claim, transcript=transcript, evidence="", label="")
        response = self.model.invoke(prompt)
        try:
            response_text = response.content if hasattr(response, "content") else str(response)
            return json.loads(response_text)
        except Exception as e:
            print(f"Entailment failed: {e}")
            return {
                "claim": claim,
                "evidence": "ERROR",
                "label": "NEUTRAL"
            }
    def detect_one(self, transcript: str, diagnosis: str, rationale: str) -> Dict[str, Any]:
        claims = self.decompose_rationale(rationale)
        entailment_labels = []
        entailment_results = []

        for claim in claims:
            result = self.attest_claim(claim, transcript)
            entailment_results.append(result)
            entailment_labels.append(result.get("label", "NEUTRAL"))

        contradiction_count = entailment_labels.count("CONTRADICTED")
        neutral_count = entailment_labels.count("NEUTRAL")
        is_hallucinated = contradiction_count > 0 or neutral_count / max(len(claims), 1) > self.threshold

        return {
            "diagnosis": diagnosis,
            "rationale": rationale,
            "claims_checked": claims,
            "entailment_results": entailment_results,
            "is_hallucinated": is_hallucinated
        }

    def __call__(self, transcript: str, diag_and_rationale: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        results = []
        for item in diag_and_rationale:
            rec = self.detect_one(transcript, item["diagnosis"], item["rationale"])
            results.append(rec)
        return results
