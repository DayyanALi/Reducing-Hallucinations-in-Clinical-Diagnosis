import os
import glob
import json
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

CLEAN_FACTS_DIR = "detectionAG/output/clean_notes_facts/gpt-4o"
NOISY_NOTES_DIR = "detectionAG/output/erroneous_notes_4o"
BASE_OUTPUT_DIR = "detectionAG/output/rq2_stability/reports/4o"
NOISY_FACTS_DIR = "detectionAG/output/noisy_facts/4o"
VALIDATION_DIR = "detectionAG/output/erroneous_notes_text"
os.makedirs(NOISY_FACTS_DIR, exist_ok=True)
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

MODELS_TO_RUN = ["gpt-5.1"]

from configs.fact_extract_prompt import *
from promptTemplate import *
from classes import FactExtractor

class StabilityAnalyst:
    def __init__(self, model_name="gpt-5.1"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model_name, api_key=api_key, temperature=0)

    def run_differential_analysis(self, clean_facts, noisy_facts):
        prompt_content = RQ2_DIFF_USER.format(
            clean_facts=json.dumps(clean_facts),
            noisy_facts=json.dumps(noisy_facts)
        )
        response = self.llm.invoke([
            {"role": "system", "content": RQ2_DIFF_SYSTEM},
            {"role": "user", "content": prompt_content}
        ])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)

def extract_noisy_fact_if_missing(noisy_path, extractor):
    noisy_id = os.path.splitext(os.path.basename(noisy_path))[0]
    fact_file = os.path.join(NOISY_FACTS_DIR, f"{noisy_id}.json")

    # ---- SKIP extraction if facts already exist ----
    if os.path.exists(fact_file):
        with open(fact_file, "r") as f:
            noisy_facts = json.load(f)
        return noisy_id, noisy_facts

    # ---- Extract facts for notes that don't exist yet ----
    with open(noisy_path, "r") as f:
        noisy_note_text = f.read()
    
    noisy_facts = extractor.to_qnote(noisy_note_text)

    with open(fact_file, "w") as f:
        json.dump(noisy_facts, f, indent=2)

    return noisy_id, noisy_facts

def run_diff(clean_facts, noisy_id, noisy_facts, analyst):
    report_path = os.path.join(BASE_OUTPUT_DIR, f"{noisy_id}_diff.json")
    if os.path.exists(report_path):
        return noisy_id, None  # already exists

    stability_report = analyst.run_differential_analysis(clean_facts, noisy_facts)

    output = {
        "meta": {
            "clean_transcript": clean_facts.get("meta", {}).get("name", "unknown"),
            "noisy_variant": noisy_id
        },
        "analysis": stability_report
    }

    with open(report_path, "w") as f:
        json.dump(output, f, indent=2)
    
    return noisy_id, output

def main():
    extractor = FactExtractor()
    clean_fact_files = sorted(glob.glob(os.path.join(CLEAN_FACTS_DIR, "*.json")))
    print(f"Found {len(clean_fact_files)} clean fact files.")

    # STEP 1: Extract all noisy facts in parallel (skip existing)
    noisy_fact_map = {}
    all_noisy_paths = []
    for clean_fact_path in clean_fact_files:
        base_name = os.path.splitext(os.path.basename(clean_fact_path))[0]
        noisy_paths = sorted(glob.glob(os.path.join(NOISY_NOTES_DIR, f"{base_name}_*.txt")))
        all_noisy_paths.extend(noisy_paths)

    print(f"Processing {len(all_noisy_paths)} noisy notes (skipping existing)...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(extract_noisy_fact_if_missing, p, extractor): p for p in all_noisy_paths}
        for future in as_completed(futures):
            noisy_id, noisy_facts = future.result()
            noisy_fact_map[noisy_id] = noisy_facts
            print(f"✅ Facts ready for {noisy_id}")

    # STEP 2: Run diffs in parallel
    for model_name in MODELS_TO_RUN:
        print(f"\nRunning differential analysis for model {model_name}...")
        analyst = StabilityAnalyst(model_name=model_name)

        tasks = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for clean_fact_path in clean_fact_files:
                base_name = os.path.splitext(os.path.basename(clean_fact_path))[0]
                with open(clean_fact_path, "r") as f:
                    clean_facts = json.load(f)

                noisy_paths = sorted(glob.glob(os.path.join(NOISY_NOTES_DIR, f"{base_name}_*.txt")))
                for noisy_path in noisy_paths:
                    noisy_id = os.path.splitext(os.path.basename(noisy_path))[0]
                    noisy_facts = noisy_fact_map.get(noisy_id)
                    if noisy_facts:
                        tasks.append(executor.submit(run_diff, clean_facts, noisy_id, noisy_facts, analyst))

            for future in as_completed(tasks):
                noisy_id, result = future.result()
                if result:
                    print(f"✅ Saved diff report for {noisy_id}")
                else:
                    print(f"[DIFF] Already exists for {noisy_id}")

if __name__ == "__main__":
    main()
