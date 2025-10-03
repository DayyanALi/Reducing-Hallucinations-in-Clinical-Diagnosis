
# detectionAG/simple_hallucination_agent.py
from __future__ import annotations
from typing import List, Dict, Any
import os, json, re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from detectionAG.configs.fact_extract_prompt import *
from detectionAG.configs.combined_detection_prompt import DETECT_ALL_SYSTEM_PROMPT, DETECT_ALL_USER_PROMPT

from dotenv import load_dotenv
load_dotenv()

SEVERITY_WEIGHTS = {2: 1, 3: 2, 4: 4, 5: 8}

class DetectionAgent:
    def __init__(self, model: str = "gpt-5-nano"):
        self.llm = ChatOpenAI(model=model)
        self.parser = JsonOutputParser()

        self.PROMPT_EXTRACT_SYSTEM = FACT_EXTRACT_SYSTEM_PROMPT
        self.PROMPT_EXTRACT_USER = FACT_EXTRACT_USER_PROMPT
        self.PROMPT_DETECT_ALL_SYSTEM = DETECT_ALL_SYSTEM_PROMPT
        self.PROMPT_DETECT_ALL_USER = DETECT_ALL_USER_PROMPT

    # ---------------- Fact Extraction ----------------
    def extract_facts(self, note_text: str) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_EXTRACT_SYSTEM),
            ("user", self.PROMPT_EXTRACT_USER),
        ])
        out = (prompt | self.llm | self.parser).invoke({"note_text": note_text})
        facts = out.get("facts", [])
        return [{"id": f["id"], "content": f["content"].strip()} for f in facts if "id" in f and "content" in f]

    # ---------------- Unified Detection ----------------
    def detect_all(self, baseline_facts: List[Dict[str, str]], candidate_facts: List[Dict[str, str]]) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_DETECT_ALL_SYSTEM),
            ("user", self.PROMPT_DETECT_ALL_USER),
        ])
        out = (prompt | self.llm | self.parser).invoke({
            "baseline_json": json.dumps(baseline_facts, ensure_ascii=False),
            "candidate_json": json.dumps(candidate_facts, ensure_ascii=False),
        })
        return {
            "hallucinations": out.get("hallucinations", []),
            "fabrications": out.get("fabrications", []),
            "critical_omissions": out.get("critical_omissions", []),
        }

    # ---------------- Label Aggregation ----------------
    def aggregate_labels(self, hallucinations, fabrications, omissions):
        labels = []
        for h in hallucinations:
            labels.append({"id": h["id"], "type": "hallucination", "severity": 4,
                           "content": h.get("content", ""), "rationale": h.get("reason", "not supported by baseline")})
        for f in fabrications:
            labels.append({"id": f["id"], "type": "fabrication", "severity": 5,
                           "content": f.get("content", ""), "rationale": f.get("reason", "implausible")})
        for o in omissions:
            labels.append({"id": o["id"], "type": "omission", "severity": 5,
                           "content": o.get("content", ""), "rationale": o.get("why", "missing critical info")})
        return labels

    # ---------------- Metrics ----------------
    # def compute_metrics(self, note_text, labels, candidate_facts):
    #     sents = re.split(r"(?<=[.!?])\s+", note_text.strip())
    #     n = max(1, len([s for s in sents if s.strip()]))

    #     fact_by_id = {f["id"]: f["content"] for f in candidate_facts}
    #     impacted = set()      
    #     per_sentence_weight = [0] * n

    #     for lb in labels:
    #         content = fact_by_id.get(lb["id"], lb.get("content", ""))
    #         for i, s in enumerate(sents):
    #             if content.lower() in s.lower():
    #                 impacted.add(i)
    #                 per_sentence_weight[i] += SEVERITY_WEIGHTS.get(lb["severity"], 0)
    #                 break

    #     deception_rate = len(impacted) / n
    #     severity_weighted = sum(per_sentence_weight) / n

    #     if deception_rate < 0.08 and severity_weighted < 0.6:
    #         risk = "Low"
    #     elif deception_rate < 0.15 and severity_weighted < 1.2:
    #         risk = "Moderate"
    #     else:
    #         risk = "High"

    #     return {
    #         "deception_rate": deception_rate,
    #         "severity_weighted": severity_weighted,
    #         "risk": risk,
    #     }
    
    def compute_metrics(self, note_text: str, labels: List[Dict[str, Any]], candidate_facts: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Deception Rate (fact-based):
            DR = (# unique candidate fact IDs that appear in labels) / (total # candidate facts)

        Severity-Weighted Score (fact-based):
            Average severity weight per candidate fact.
        """
        # --- Fact-based deception rate ---
        total_candidate_facts = max(1, len(candidate_facts))
        flagged_ids = {lb["id"] for lb in labels if lb.get("id")}
        deception_rate = len(flagged_ids) / total_candidate_facts

        # --- Fact-based severity weighted score ---
        total_severity = sum(SEVERITY_WEIGHTS.get(lb.get("severity", 0), 0) for lb in labels)
        severity_weighted = total_severity / total_candidate_facts

        # --- Risk bucketing (uses both DR and SWS) ---
        if deception_rate < 0.08 and severity_weighted < 0.6:
            risk = "Low"
        elif deception_rate < 0.15 and severity_weighted < 1.2:
            risk = "Moderate"
        else:
            risk = "High"

        return {
            "deception_rate": deception_rate,        # fact-based
            "severity_weighted": severity_weighted,  # now fact-based
            "risk": risk,
        }


    # ---------------- Orchestrator ----------------
    def run_all(self, baseline_text: str, candidate_text: str) -> Dict[str, Any]:
        # print("strting run_all")
        base_facts = self.extract_facts(baseline_text)
        cand_facts = self.extract_facts(candidate_text)
        # print("facts extracted")

        detected = self.detect_all(base_facts, cand_facts)
        # print("detected")
        labels = self.aggregate_labels(detected["hallucinations"], detected["fabrications"], detected["critical_omissions"])
        metrics = self.compute_metrics(candidate_text, labels, cand_facts)

        return {
            "baseline_facts": base_facts,
            "candidate_facts": cand_facts,
            **detected,
            "labels": labels,
            "metrics": metrics,
        }
        
if __name__ == "__main__":
    import os
    import re
    from pathlib import Path

    # --- Configurable paths ---
    NOTES_DIR = Path("detectionAG/output/notes_markdown")
    TRANS_DIR = Path("detectionAG/output/transcriptions")
    # TRANS_DIR = Path("data/babylon_data/generated_joined_transcripts")
    OUT_DIR = Path("detectionAG/output/evaluations_set2")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def natural_key(s: str):
        """Sort like humans: file2 < file10."""
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

    # Collect and sort files
    note_files = sorted([p for p in NOTES_DIR.glob("*.txt")], key=lambda p: natural_key(p.name))
    trans_files = sorted([p for p in TRANS_DIR.glob("*.txt")], key=lambda p: natural_key(p.name))

    if not note_files:
        raise FileNotFoundError(f"No .txt files found in {NOTES_DIR}")
    if not trans_files:
        raise FileNotFoundError(f"No .txt files found in {TRANS_DIR}")

    # Use the first 5 of each, paired by index
    n = min(5, len(note_files), len(trans_files))
    pairs = list(zip(note_files[:n], trans_files[:n]))

    # Init agent once
    agent = DetectionAgent(model="gpt-5-nano")

    all_summaries = []
    for i, (note_path, trans_path) in enumerate(pairs, start=1):
        with open(note_path, "r", encoding="utf-8") as f:
            generated_note = f.read()
        with open(trans_path, "r", encoding="utf-8") as f:
            transcript = f.read()

        print(f"[{i}/{n}] Evaluating note={note_path.name} vs transcript={trans_path.name} ...")
        try:
            result = agent.run_all(transcript, generated_note)
        except Exception as e:
            # If something fails, write an error record and continue
            result = {
                "error": str(e),
                "note_file": note_path.name,
                "transcript_file": trans_path.name,
            }

        # Write a per-pair JSON
        out_name = f"result_{note_path.stem}__{trans_path.stem}.json"
        out_path = OUT_DIR / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        all_summaries.append({
            "note_file": note_path.name,
            "transcript_file": trans_path.name,
            "output_file": out_path.name
        })

    # Optionally write an index file listing all outputs
    index_path = OUT_DIR / "index_first5.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"pairs": all_summaries}, f, indent=2, ensure_ascii=False)

    print(f"Done. Wrote {n} result files to: {OUT_DIR}")


