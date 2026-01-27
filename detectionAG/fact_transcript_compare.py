import os
import json
import re
import random
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from tqdm import tqdm

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import your prompts (Make sure this file exists in your configs folder)
from configs.fact_extract_prompt import FACT_VERIFY_SYSTEM_PROMPT, FACT_VERIFY_USER_PROMPT

load_dotenv()

# --- CONFIGURATION ---
VERIFIER_MODEL = "gpt-5.1"  # Use a real model name (gpt-5.1 isn't public yet)
OVERWRITE = False

class FactVerifier:
    def __init__(self, model: str = VERIFIER_MODEL):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}},
            max_retries=3
        )
        self.parser = JsonOutputParser()

    def verify_facts(self, transcript_text: str, gen_facts: List[Dict]) -> Dict:
        if not gen_facts:
            return {"verdict": []}

        prompt = ChatPromptTemplate.from_messages([
            ("system", FACT_VERIFY_SYSTEM_PROMPT),
            ("user", FACT_VERIFY_USER_PROMPT),
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            # Send simplified facts to save tokens
            slim_facts = [{"fact_id": f["id"], "content": f["content"]} for f in gen_facts]
            
            return chain.invoke({
                "transcript": transcript_text,
                "facts_json": json.dumps(slim_facts, indent=1)
            })
        except Exception as e:
            return {"error": str(e), "verdict": []}

def extract_consultation_id(filename: str) -> str:
    # Matches "day1_consultation01" inside filenames like "facts_day1_consultation01.json"
    match = re.search(r"(day\d+_consultation\d+)", filename)
    if match:
        return match.group(1)
    return None

# --- WORKER FUNCTION ---
def process_verification(gen_path: Path, trans_path: Path, output_root: Path, verifier: FactVerifier):
    try:
        # AUTOMATICALLY DETECT MODEL NAME FROM FOLDER
        # If path is .../extracted_facts_reasoning/gpt-5_high/facts_day1... 
        # parent.name is "gpt-5_high"
        model_name = gen_path.parent.name 
        
        # Setup Output Directory (e.g., .../verifications/gpt-5_high/)
        target_dir = output_root / model_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        cid = extract_consultation_id(gen_path.name)
        out_name = f"verification_{cid}.json"
        out_path = target_dir / out_name
        
        if not OVERWRITE and out_path.exists():
            return "Skipped"

        # Load Transcript
        with open(trans_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
            
        # Load Generated Facts
        with open(gen_path, 'r', encoding='utf-8') as f:
            gen_data = json.load(f)
            facts = gen_data.get('facts', [])

        # Run Verification
        result = verifier.verify_facts(transcript_text, facts)
        
        if "error" in result:
             return f"Error from LLM: {result['error']}"

        # Calculate Metrics
        stats = {"SUPPORTED": 0, "ADDITION": 0, "CONTRADICTION": 0}
        for v in result.get("verdict", []):
            status = v.get("status", "UNKNOWN")
            if status in stats:
                stats[status] += 1
        
        total = len(result.get("verdict", []))
        
        final_report = {
            "file_id": gen_data.get("source_file"),
            "model_source": model_name, # Storing the folder name as the model source
            "transcript_ref": trans_path.name,
            "metrics": {
                "total_facts": total,
                "supported_count": stats["SUPPORTED"],
                "addition_count": stats["ADDITION"],
                "contradiction_count": stats["CONTRADICTION"],
                "hallucination_rate": round((stats["ADDITION"] + stats["CONTRADICTION"]) / total, 4) if total > 0 else 0
            },
            "verdict": result.get("verdict", [])
        }

        # Save
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2)
            
        return "Success"

    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN ---
if __name__ == "__main__":
    
    # 1. SETUP PATHS
    BASE_PATH = Path("E:/hallucination/Reducing-Hallucinations-in-Clinical-Diagnosis")
    
    # Points to the folder containing model subfolders (gpt-5_high, gpt-4, etc.)
    GEN_ROOT = BASE_PATH / "detectionAG/experiements/extracted_facts_reasoning"
    
    # Points to raw transcripts
    TRANS_DIR = BASE_PATH / "data/babylon_data/babylonhealth primock57 main transcripts combined" 
    
    # Output location
    OUTPUT_ROOT = BASE_PATH / "experiements/verifications_vs_transcript_reasoning"
    
    # 2. Index Transcripts
    print(f"Indexing Transcripts from: {TRANS_DIR}")
    trans_index = {}
    if not TRANS_DIR.exists():
        print(f"CRITICAL ERROR: Transcript directory not found at {TRANS_DIR}")
        exit()

    for p in TRANS_DIR.glob("*.txt"):
        cid = extract_consultation_id(p.name)
        if cid:
            trans_index[cid] = p
            
    print(f"Found {len(trans_index)} Transcripts.")

    # 3. Gather Tasks (Recursive Search)
    print(f"Gathering generated fact files from: {GEN_ROOT}")
    all_tasks = []
    
    # rglob("*.json") searches recursively through all model subfolders
    for gen_path in GEN_ROOT.rglob("*.json"):
        cid = extract_consultation_id(gen_path.name)
        
        # Link Gen Fact -> Transcript
        if cid and cid in trans_index:
            trans_path = trans_index[cid]
            all_tasks.append((gen_path, trans_path))
        elif cid:
            print(f"Warning: No transcript found for {cid} (File: {gen_path.name})")
            
    random.shuffle(all_tasks)
    print(f"Found {len(all_tasks)} pairs to verify across all models.")

    # 4. Run
    verifier = FactVerifier(model=VERIFIER_MODEL)
    stats_counter = {"Success": 0, "Skipped": 0, "Error": 0}

    # REMOVED the [:5] slice so it runs everything
    for gen_path, trans_path in tqdm(all_tasks):
        status = process_verification(gen_path, trans_path, OUTPUT_ROOT, verifier)
        
        if status == "Success": stats_counter["Success"] += 1
        elif status == "Skipped": stats_counter["Skipped"] += 1
        else: 
            stats_counter["Error"] += 1
            print(f"Failed {gen_path.name}: {status}")

    print(f"\nDone. Stats: {stats_counter}")