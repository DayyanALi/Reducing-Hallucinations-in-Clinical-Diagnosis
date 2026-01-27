import os
import json
import re
import random
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from tqdm import tqdm

##############################################
# Note to Note Facts Comparison
##############################################

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import the prompt
from configs.fact_extract_prompt import FACT_COMPARE_SYSTEM_PROMPT, FACT_COMPARE_USER_PROMPT

load_dotenv()

# --- CONFIGURATION ---
COMPARATOR_MODEL = "gpt-5.1"  # The "Judge" Model
OVERWRITE = False             # Set True to re-run existing comparisons

class NoteComparator:
    def __init__(self, model: str = COMPARATOR_MODEL):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}},
            max_retries=3
        )
        self.parser = JsonOutputParser()

    def _flatten_gold_dict(self, gold_data: Dict[str, Any]) -> List[Dict]:
        flat_gold = []
        for section, facts in gold_data.items():
            if isinstance(facts, list):
                for fact in facts:
                    f_copy = fact.copy()
                    if 'section' not in f_copy:
                        f_copy['section'] = section
                    flat_gold.append(f_copy)
        return flat_gold

    def compare_fact_sets(self, section_context: str, gold_facts: List[Dict], gen_facts: List[Dict]) -> Dict:
        if not gold_facts and not gen_facts:
            return {"gold_assessment": [], "gen_assessment": []}

        prompt = ChatPromptTemplate.from_messages([
            ("system", FACT_COMPARE_SYSTEM_PROMPT),
            ("user", FACT_COMPARE_USER_PROMPT),
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            return chain.invoke({
                "section_name": section_context,
                "gold_facts": json.dumps(gold_facts, indent=1),
                "gen_facts": json.dumps(gen_facts, indent=1)
            })
        except Exception as e:
            # print(f"Error comparing facts: {e}")
            return {"error": str(e), "gold_assessment": [], "gen_assessment": []}

    def compare_full_note(self, gold_data: Dict, gen_data: Dict) -> Dict:
        flat_gold_facts = self._flatten_gold_dict(gold_data)
        flat_gen_facts = gen_data.get('facts', [])
        
        full_report = {
            "file_id": gen_data.get("source_file"),
            "model_source": gen_data.get("model_source"),
            "metrics": {},
            "raw_assessment": {}
        }

        # Run Comparison
        result = self.compare_fact_sets("ENTIRE_CLINICAL_NOTE", flat_gold_facts, flat_gen_facts)
        full_report["raw_assessment"] = result

        if "error" in result:
            return full_report # Return partial report on error

        # Calculate Metrics
        total_gold = 0
        total_omitted = 0
        total_gen = 0
        total_contradictions = 0
        total_additions = 0

        for item in result.get("gold_assessment", []):
            total_gold += 1
            if item["status"] == "OMITTED":
                total_omitted += 1
        
        for item in result.get("gen_assessment", []):
            total_gen += 1
            if item["status"] == "CONTRADICTION":
                total_contradictions += 1
            elif item["status"] == "ADDITION":
                total_additions += 1

        omission_rate = (total_omitted / total_gold) if total_gold > 0 else 0.0
        contradiction_rate = (total_contradictions / total_gen) if total_gen > 0 else 0.0
        addition_rate = (total_additions / total_gen) if total_gen > 0 else 0.0

        full_report["metrics"] = {
            "total_gold_facts": total_gold,
            "total_gen_facts": total_gen,
            "omission_count": total_omitted,
            "omission_rate": round(omission_rate, 4),
            "contradiction_count": total_contradictions,
            "contradiction_rate": round(contradiction_rate, 4),
            "addition_count": total_additions,
            "addition_rate": round(addition_rate, 4)
        }

        return full_report

def extract_consultation_id(filename: str, erroneous=False) -> str:
    if erroneous:
        # Match facts_day1_consultation12_error_130.json
        match = re.search(r"facts_(day\d+_consultation\d+)_error_\d+\.json", filename)
    else:
        match = re.search(r"(day\d+_consultation\d+)", filename)
    print("match for ", filename, " :  ", match)
    if match:
        return match.group(1)
    return None

# --- WORKER FUNCTION (Called sequentially) ---
def process_single_pair(gen_path: Path, gold_path: Path, output_root: Path, comparator: NoteComparator):
    try:
        # Determine Model Name from the folder structure
        # gen_path = .../extracted_facts/gpt-4.1/facts_file.json
        # model_name = gen_path.parent.name
        model_name = "gpt-5" # Hardcoded for one-to-many erroneous notes comparison       
        gen_stem = gen_path.stem[6:]  # Remove 'facts_' prefix
        print("genstem: ", gen_stem)
        
        # Ensure output directory exists for this model
        target_dir = output_root / model_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output filename
        out_name = f"{gen_stem}.json"
        out_path = target_dir / out_name
        
        # Resume Logic
        if not OVERWRITE and out_path.exists():
            return "Skipped"

        # Load Data
        with open(gold_path, 'r', encoding='utf-8') as f:
            gold_data = json.load(f)
        with open(gen_path, 'r', encoding='utf-8') as f:
            gen_data = json.load(f)

        # Run Comparison
        report = comparator.compare_full_note(gold_data, gen_data)
        
        # Save
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        return "Success"

    except Exception as e:
        return f"Error: {str(e)}"
    
def run_all_one_to_one_comparisons():
    BASE_PATH = Path(__file__).resolve().parents[1]  
    
    # 1. Paths
    # Note: Scanning the ROOT of extracted_facts to find all model folders
    GEN_ROOT = BASE_PATH / "detectionAG/output/extracted_facts"
    GOLD_DIR = BASE_PATH / "data/babylon_data/babylon_notes_facts"
    OUTPUT_ROOT = BASE_PATH / "detectionAG/output/comparisons"
    
    # 2. Index Gold Files
    print(f"Indexing Gold Files...")
    gold_index = {}
    try:
        for p in GOLD_DIR.glob("*.json"):
            cid = extract_consultation_id(p.name)
            if cid:
                gold_index[cid] = p
    except Exception as e:
        print(f"Error reading Gold Directory: {e}")
        exit()
    print(f"Found {len(gold_index)} Gold References.")

    # 3. Gather All Generated Files (Recursive)
    print("Gathering generated fact files from all models...")
    all_tasks = []
    
    # Use rglob to find all .json files in subdirectories
    for gen_path in GEN_ROOT.rglob("*.json"):
        cid = extract_consultation_id(gen_path.name)
        
        # Only add task if we have a matching gold file
        if cid and cid in gold_index:
            gold_path = gold_index[cid]
            all_tasks.append((gen_path, gold_path))
            
    # Shuffle to mix models during processing (helps with rate limit distribution)
    random.shuffle(all_tasks)
    
    print(f"Found {len(all_tasks)} valid pairs to compare.")
    print(f"Comparator Model: {COMPARATOR_MODEL}")
    print(f"Mode: Sequential Execution")
    print("tasks:", all_tasks)

    # 4. Initialize Comparator
    comparator = NoteComparator(model=COMPARATOR_MODEL)

    # 5. Execution
    stats = {"Success": 0, "Skipped": 0, "Error": 0}
    
    # Sequential Loop
    for gen_path, gold_path in tqdm(all_tasks):
        try:
            status = process_single_pair(gen_path, gold_path, OUTPUT_ROOT, comparator)
            
            if status == "Success":
                stats["Success"] += 1
            elif status == "Skipped":
                stats["Skipped"] += 1
            else:
                stats["Error"] += 1
                # tqdm.write(f"[{gen_path.parent.name}] {gen_path.name}: {status}")
                
        except Exception as e:
            stats["Error"] += 1
            print(f"Critical Failure on {gen_path.name}: {e}")

    print("\n--- Benchmarking Complete ---")
    print(f"Summary: {stats}")
    print(f"Results saved to: {OUTPUT_ROOT}")

def run_all_one_to_many_comparisons():
    # ---- Paths ----
    GEN_ROOT = Path("detectionAG/output/erroneous_note_facts")
    GOLD_DIR = Path("data/babylon_data/babylon_notes_facts")
    OUTPUT_ROOT = Path("detectionAG/output/erroneous_note_gold_comparisons")

    # ---- Index gold files ----
    print("Indexing Gold Files...")
    gold_index: Dict[str, Path] = {}

    for p in GOLD_DIR.glob("*.json"):
        cid = extract_consultation_id(p.name)
        if cid:
            gold_index[cid] = p

    print(f"Found {len(gold_index)} gold references.")
    print("----- GOLD FILES: ")
    print(gold_index)

    # ---- Index generated files (MULTIPLE per CID) ----
    print("Indexing generated fact files...")
    gen_index: Dict[str, List[Path]] = {}

    for gen_path in GEN_ROOT.rglob("*.json"):
        print("genpath: ", gen_path)
        cid = extract_consultation_id(gen_path.name, erroneous=True)
        if not cid:
            continue
        gen_index.setdefault(cid, []).append(gen_path)

    print(f"Found generated notes for {len(gen_index)} consultations.")

    # ---- Build tasks: gold vs MANY generated (erroneous files) ----
    all_tasks = []

    for cid, gold_path in gold_index.items():
        for gen_path in gen_index.get(cid, []):
            all_tasks.append((gen_path, gold_path))

    random.shuffle(all_tasks)
    print("------all tasks:\n", all_tasks)

    print(f"Total comparisons to run: {len(all_tasks)}")
    print(f"Comparator Model: {COMPARATOR_MODEL}")
    print("Mode: Sequential Execution")

    # # ---- Run ----
    comparator = NoteComparator(model=COMPARATOR_MODEL)

    stats = {"Success": 0, "Skipped": 0, "Error": 0}

    for gen_path, gold_path in tqdm(all_tasks):
        status = process_single_pair(
            gen_path,
            gold_path,
            OUTPUT_ROOT,
            comparator,
        )

        if status == "Success":
            stats["Success"] += 1
        elif status == "Skipped":
            stats["Skipped"] += 1
        else:
            stats["Error"] += 1

    print("\n--- Benchmarking Complete ---")
    print(f"Summary: {stats}")
    print(f"Results saved to: {OUTPUT_ROOT}")

# --- MAIN ---
if __name__ == "__main__":
    run_all_one_to_many_comparisons()