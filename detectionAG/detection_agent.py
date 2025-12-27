
# detectionAG/simple_hallucination_agent.py
from __future__ import annotations
from typing import List, Dict, Any
import os, json, re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from configs.fact_extract_prompt import *
from configs.combined_detection_prompt import DETECT_ALL_SYSTEM_PROMPT, DETECT_ALL_USER_PROMPT

from dotenv import load_dotenv
load_dotenv()

SEVERITY_WEIGHTS = {2: 1, 3: 2, 4: 4, 5: 8}

class DetectionAgent:
    def __init__(self, model: str = "gpt-5-nano"):
        self.llm = ChatOpenAI(model=model)
        self.parser = JsonOutputParser()

        self.PROMPT_EXTRACT_SYSTEM = NOTE_FACT_EXTRACT_SYSTEM_PROMPT
        self.PROMPT_EXTRACT_USER = NOTE_FACT_EXTRACT_USER_PROMPT
        self.PROMPT_DETECT_ALL_SYSTEM = DETECT_ALL_SYSTEM_PROMPT
        self.PROMPT_DETECT_ALL_USER = DETECT_ALL_USER_PROMPT

    # ---------------- Fact Extraction ----------------
    def extract_facts(self, note_text: str) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_EXTRACT_SYSTEM),
            ("user", self.PROMPT_EXTRACT_USER),
        ])
        out = (prompt | self.llm | self.parser).invoke({"note": note_text})
        print("out: ", out)
        facts = out.get("facts", [])
        return [{"fact_id": f["fact_id"], "content": f["content"].strip(), "source_text": f["source_text"].strip()} for f in facts if "id" in f and "content" in f and "source_text" in f]

    # ---------------- Transcript Fact Extraction ----------------
    def transcript_extract_facts(self, transcript_text: str) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_EXTRACT_SYSTEM),
            ("user", self.PROMPT_EXTRACT_USER),
        ])
        out = (prompt | self.llm | self.parser).invoke({"transcript": transcript_text})
        facts = out.get("facts", [])
        return facts

    # ---------------- Note Fact Extraction ----------------
    def extract_note_facts(self, note_text: str) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_EXTRACT_SYSTEM),
            ("user", self.PROMPT_EXTRACT_USER),
        ])

        out = (prompt | self.llm | self.parser).invoke(
            {"note": note_text}
        )

        facts = []
        print("type: ",type(out))

        if isinstance(out, dict):
            for section_name, section_facts in out.items():
                if isinstance(section_facts, list):
                    for fact in section_facts:
                        if isinstance(fact, dict):
                            # Enforce section = top-level key
                            fact = fact.copy()
                            fact["section"] = section_name
                            facts.append(fact)

        return facts

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

def run_transcript_fact_extraction():
    import os
    import re
    import json
    from pathlib import Path

    # --- Configurable paths ---
    TRANS_DIR = Path("data/babylon_data_cleaned/babylonhealth primock57 main transcripts combined")
    OUT_DIR = Path("detectionAG/output/transcript_facts")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def natural_key(s: str):
        """Sort like humans (file2 < file10)."""
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

    # Collect and sort files
    transcript_files = sorted([p for p in TRANS_DIR.glob("*.txt")], key=lambda p: natural_key(p.name))

    if not transcript_files:
        raise FileNotFoundError(f"No .txt files found in {TRANS_DIR}")

    # Init agent once
    agent = DetectionAgent(model="gpt-5")

    all_outputs = []
    for i, transcript_path in enumerate(transcript_files, start=1):
        out_path = OUT_DIR / f"facts_{transcript_path.stem}.json"

        # --- Skip if output file exists and contains "facts" key ---
        if out_path.exists():
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "facts" in data:
                    print(f"[{i}/{len(transcript_files)}] Skipping {transcript_path.name}, output already exists with facts.")
                    all_outputs.append({
                        "note_file": transcript_path.name,
                        "output_file": out_path.name
                    })
                    continue
            except Exception:
                # If file exists but is corrupted or invalid JSON, re-run extraction
                pass

        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()

        print(f"[{i}/{len(transcript_files)}] Extracting facts from note={transcript_path.name} ...")
        try:
            facts = agent.transcript_extract_facts(transcript_text)
            result = {
                "transcript_file": transcript_path.name,
                "facts": facts
            }
        except Exception as e:
            result = {
                "transcript_file": transcript_path.name,
                "error": str(e)
            }

        # Write JSON output
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        all_outputs.append({
            "transcript_file": transcript_path.name,
            "output_file": out_path.name
        })

    # Write index file
    index_path = OUT_DIR / "index_facts.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"outputs": all_outputs}, f, indent=2, ensure_ascii=False)

    print(f"Done. Wrote results to: {OUT_DIR}")
    
def run_note_vs_transcript_comparisons():
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

def run_note_fact_extraction():
    import os
    import re
    import json
    from pathlib import Path

    # --- Configurable paths ---
    NOTES_DIR = Path("detectionAG/output/erroneous_notes_text")
    OUT_DIR = Path("detectionAG/output/erroneous_note_facts")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect files
    note_files = [p for p in NOTES_DIR.glob("*.txt")]

    if not note_files:
        raise FileNotFoundError(f"No .txt files found in {NOTES_DIR}")

    # Init agent once
    agent = DetectionAgent(model="gpt-5")

    all_outputs = []
    for i, note_path in enumerate(note_files, start=1):
        if i == 10:
            break
        out_path = OUT_DIR / f"facts_{note_path.stem}.json"
        print(f"--------Processing {note_path}")

        # --- Skip if output file exists and contains "facts" key ---
        if out_path.exists():
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "facts" in data:
                    print(f"[{i}/{len(note_files)}] Skipping {note_path.name}, output already exists with facts.")
                    all_outputs.append({
                        "note_file": note_path.name,
                        "output_file": out_path.name
                    })
                    continue
            except Exception:
                # If file exists but is corrupted or invalid JSON, re-run extraction
                pass

        with open(note_path, "r", encoding="utf-8") as f:
            note_text = f.read()

        print(f"[{i}/{len(note_files)}] Extracting facts from note={note_path.name} ...")
        try:
            facts = agent.extract_note_facts(note_text)
            result = {
                "note_file": note_path.name,
                "facts": facts,
                "fact_count": len(facts),
                "model_source": "gpt-5"
            }
        except Exception as e:
            result = {
                "note_file": note_path.name,
                "error": str(e)
            }

        # Write JSON output
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        all_outputs.append({
            "note_file": note_path.name,
            "output_file": out_path.name
        })

    # Write index file
    index_path = OUT_DIR / "index_facts.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"outputs": all_outputs}, f, indent=2, ensure_ascii=False)

    print(f"Done. Wrote results to: {OUT_DIR}")
    

if __name__ == "__main__":
    run_note_fact_extraction()