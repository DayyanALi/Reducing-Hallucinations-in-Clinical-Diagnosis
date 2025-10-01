import re
import time
import pandas as pd
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any

from promptTemplate import (
    LINGUISTIC_QUALITY_PROMPT,
    CONTENT_INTEGRITY_PROMPT,
    TRUSTWORTHINESS_PROMPT
)

@dataclass
class EvaluationResult:
    evaluation_type: str
    dimension: str
    yes_no: str
    score: int
    explanation: str

class MedicalNoteEvaluator:
    def __init__(self, api_key: str, model_name: str = "gpt-5-nano", temperature: float = 0.7):

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )

        self.linguistic_quality_prompt = LINGUISTIC_QUALITY_PROMPT
        self.content_integrity_prompt = CONTENT_INTEGRITY_PROMPT
        self.trustworthiness_prompt = TRUSTWORTHINESS_PROMPT

    def _parse_evaluation_output(self, output: str, dimensions: List[str]) -> Dict[str, Dict[str, Any]]:

        parsed_res = {}
        
        section_pattern = f'"({"|".join(dimensions)})":\\s*\\{{(.*?)\\}}'
        matches = re.findall(section_pattern, output, re.DOTALL)
        
        for section, content in matches:
            yes_no_match = re.search(r'"Yes/No":\s*"([^"]*)"', content)
            score_match = re.search(r'"Score":\s*(\d+)', content)
            explanation_match = re.search(r'"Explanation":\s*"([^"]*)"', content, re.DOTALL)
            
            if not all([yes_no_match, score_match, explanation_match]):
                print(f"Warning: Missing field in section {section}")
                continue
                
            parsed_res[section] = {
                "Yes/No": yes_no_match.group(1),
                "Score": int(score_match.group(1)),
                "Explanation": explanation_match.group(1).strip()
            }
            
        return parsed_res

    def _evaluate_linguistic_quality(self, physician_note: str, ai_note: str) -> Dict[str, Dict[str, Any]]:

        prompt = self.linguistic_quality_prompt.format(
            physician_note=physician_note,
            ai_medical_note=ai_note
        )
        response = self.llm.invoke(prompt).content
        return self._parse_evaluation_output(
            response,
            ["Fluency", "Coherence", "Clarity", "Brevity", "Structuring"]
        )

    def _evaluate_content_integrity(self, physician_note: str, ai_note: str) -> Dict[str, Dict[str, Any]]:

        prompt = self.content_integrity_prompt.format(
            physician_note=physician_note,
            ai_medical_note=ai_note
        )
        response = self.llm.invoke(prompt).content
        return self._parse_evaluation_output(
            response,
            ["Relevance", "Completeness", "Factuality", "Comprehension"]
        )

    def _evaluate_trustworthiness(self, physician_note: str, ai_note: str) -> Dict[str, Dict[str, Any]]:

        prompt = self.trustworthiness_prompt.format(
            physician_note=physician_note,
            ai_medical_note=ai_note
        )
        response = self.llm.invoke(prompt).content
        return self._parse_evaluation_output(
            response,
            ["Prudence", "Toxicity", "Bias", "Fairness"]
        )

    def _integrate_result(
        self,
        linguistic_quality: Dict[str, Dict[str, Any]],
        content_integrity: Dict[str, Dict[str, Any]],
        trustworthiness: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        result = {}
        
        for dimension, data in linguistic_quality.items():
            prefix = f"Linguistic Quality_{dimension}"
            result[f"{prefix}_Yes/No"] = data["Yes/No"]
            result[f"{prefix}_Score"] = data["Score"]
            result[f"{prefix}_Explanation"] = data["Explanation"]

        for dimension, data in content_integrity.items():
            prefix = f"Content Integrity_{dimension}"
            result[f"{prefix}_Yes/No"] = data["Yes/No"]
            result[f"{prefix}_Score"] = data["Score"]
            result[f"{prefix}_Explanation"] = data["Explanation"]
            
        for dimension, data in trustworthiness.items():
            prefix = f"Trustworthiness_{dimension}"
            result[f"{prefix}_Yes/No"] = data["Yes/No"]
            result[f"{prefix}_Score"] = data["Score"]
            result[f"{prefix}_Explanation"] = data["Explanation"]
            
        return pd.DataFrame([result])

    def evaluate_note_text(self, physician_note: str, ai_note: str) -> pd.DataFrame:
        """
        Evaluate medical notes when provided directly as text (not file paths).
        """
        try:
            start_time = time.time()

            linguistic_quality = self._evaluate_linguistic_quality(physician_note, ai_note)
            content_integrity = self._evaluate_content_integrity(physician_note, ai_note)
            trustworthiness = self._evaluate_trustworthiness(physician_note, ai_note)

            result = self._integrate_result(
                linguistic_quality,
                content_integrity,
                trustworthiness
            )

            end_time = time.time()
            elapsed_time = end_time - start_time
            result["Efficiency"] = round(elapsed_time, 2)

            return pd.DataFrame(result)

        except Exception as e:
            raise Exception(f"Evaluation (text) failed: {str(e)}")
