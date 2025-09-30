# simple_hallucination_agent.py
from __future__ import annotations
from typing import List, Dict, Any
import os, json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from detectionAG.configs.fabrication_prompt import *
from detectionAG.configs.hallucination_detect_prompt import *
from detectionAG.configs.omission_prompt import *
from detectionAG.configs.fact_extract_prompt import *

from dotenv import load_dotenv

load_dotenv()

class SimpleHallucinationAgent:
    def __init__(self, model: str = "gpt-5-nano", temperature: float = 0.0):
        self.llm = ChatOpenAI(model=model, temperature=temperature)

        # ---------- PROMPTS (as requested: explicit strings, no functions) ----------
        # 1) Extract facts (keep them simple)
        self.PROMPT_EXTRACT_SYSTEM = FACT_EXTRACT_SYSTEM_PROMPT
        self.PROMPT_EXTRACT_USER = FACT_EXTRACT_USER_PROMPT

        # 2) Factual hallucination: candidate facts not supported by baseline facts
        self.PROMPT_HALLUCINATION_SYSTEM = HALLUCINATION_SYSTEM_PROMPT
        self.PROMPT_HALLUCINATION_USER = HALLUCINATION_USER_PROMPT

        # 3) Medical fabrication: internally implausible/impossible candidate facts
        self.PROMPT_FABRICATION_SYSTEM = FABRICATION_SYSTEM_PROMPT
        self.PROMPT_FABRICATION_USER = FABRICATION_USER_PROMPT

        # 4) Critical omission: important baseline facts missing from candidate
        self.PROMPT_OMISSION_SYSTEM = OMISSION_SYSTEM_PROMPT
        self.PROMPT_OMISSION_USER = OMISSION_USER_PROMPT

        # Reusable JSON parser (will raise if not valid JSON)
        self.parser = JsonOutputParser()

    # ---------------- Public methods ----------------

    def extract_facts(self, note_text: str) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_EXTRACT_SYSTEM),
            ("user", self.PROMPT_EXTRACT_USER),
        ])
        chain = prompt | self.llm | self.parser
        out = chain.invoke({"note_text": note_text})
        # Expect {"facts":[{"id":"F1","content":"..."}, ...]}
        facts = out.get("facts", [])
        # Ensure structure
        cleaned = [{"id": str(f["id"]), "content": str(f["content"]).strip()} for f in facts if "id" in f and "content" in f]
        return cleaned

    def check_hallucination(self, baseline_facts: List[Dict[str, str]], candidate_facts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_HALLUCINATION_SYSTEM),
            ("user", self.PROMPT_HALLUCINATION_USER),
        ])
        chain = prompt | self.llm | self.parser
        out = chain.invoke({
            "baseline_json": json.dumps(baseline_facts, ensure_ascii=False),
            "candidate_json": json.dumps(candidate_facts, ensure_ascii=False),
        })
        # Expect {"hallucinations":[{"id":"<candidate_id>","content":"..."}, ...]}
        return out.get("hallucinations", [])

    def check_medical_fabrication(self, candidate_facts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_FABRICATION_SYSTEM),
            ("user", self.PROMPT_FABRICATION_USER),
        ])
        chain = prompt | self.llm | self.parser
        out = chain.invoke({
            "candidate_json": json.dumps(candidate_facts, ensure_ascii=False),
        })
        # Expect {"fabrications":[{"id":"<candidate_id>","content":"...","reason":"..."}]}
        return out.get("fabrications", [])

    def check_critical_omission(self, baseline_facts: List[Dict[str, str]], candidate_facts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_OMISSION_SYSTEM),
            ("user", self.PROMPT_OMISSION_USER),
        ])
        chain = prompt | self.llm | self.parser
        out = chain.invoke({
            "baseline_json": json.dumps(baseline_facts, ensure_ascii=False),
            "candidate_json": json.dumps(candidate_facts, ensure_ascii=False),
        })
        # Expect {"critical_omissions":[{"id":"<baseline_id>","content":"...","why":"..."}]}
        return out.get("critical_omissions", [])

    def run_all(self, baseline_text: str, candidate_text: str) -> Dict[str, Any]:
        base_facts = self.extract_facts(baseline_text)
        cand_facts = self.extract_facts(candidate_text)
        hallucinations = self.check_hallucination(base_facts, cand_facts)
        fabrications = self.check_medical_fabrication(cand_facts)
        omissions = self.check_critical_omission(base_facts, cand_facts)
        return {
            "baseline_facts": base_facts,
            "candidate_facts": cand_facts,
            "hallucinations": hallucinations,
            "fabrications": fabrications,
            "critical_omissions": omissions,
        }


if __name__ == "__main__":
    """
    QUICK DEMO
    Set your API key first:
        export OPENAI_API_KEY=sk-...
    """
    baseline = """
    Patient denies chest pain. Reports dry cough x 7 days. HR 110 bpm, BP 120/80.
    Penicillin allergy documented. Assessment: Viral URI suspected. Plan: Rest, fluids.
    """
    candidate = """
    Patient reports chest pain and cough for one week. Heart rate 250 bpm. No mention of allergies.
    Assessment: Viral URI. Plan: Rest and fluids.
    """

    agent = SimpleHallucinationAgent(model="gpt-5-nano", temperature=0.0)

    result = agent.run_all(baseline, candidate)
    print(json.dumps(result, indent=2, ensure_ascii=False))
