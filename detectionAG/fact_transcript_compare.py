import os
import json
import re
import random
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from tqdm import tqdm

##############################################
# Raw Note Facts to Transcript Comparison
##############################################

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import the new prompt
from configs.fact_extract_prompt import FACT_VERIFY_SYSTEM_PROMPT, FACT_VERIFY_USER_PROMPT

load_dotenv() 

# --- CONFIGURATION ---
VERIFIER_MODEL = "gpt-5.1"  # Needs a smart model for entailment
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
        """
        Sends the transcript and the list of facts to the LLM for verification.
        """
        if not gen_facts:
            return {"verdict": []}

        # Optimization: If facts list is huge (>50), chunking might be needed. 
        # For now, we assume <50 facts fits in context.
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", FACT_VERIFY_SYSTEM_PROMPT),
            ("user", FACT_VERIFY_USER_PROMPT),
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            # We strip the 'source_text' from gen_facts to save tokens, 
            # the verifier only needs the 'content' claim.
            slim_facts = [{"fact_id": f["fact_id"], "content": f["content"]} for f in gen_facts]
            
            return chain.invoke({
                "transcript": transcript_text,
                "facts_json": json.dumps(slim_facts, indent=1)
            })
        except Exception as e:
            return {"error": str(e), "verdict": []}

def extract_consultation_id(filename: str) -> str: # Matches "*day1_consultation01*" 
    match = re.search(r"(day\d+_consultation\d+)", filename) 
    if match: 
        return match.group(1)
    return None

def extract_error_number(filename: str) -> int:
    """
    Extracts the last number before the extension in the filename.
    Example:
        day1_consultation04_change130.txt -> 130
        facts_day1_consultation04_error131.json -> 131
    """
    match = re.search(r"(\d+)(?=\.\w+$)", filename)
    if match:
        return int(match.group(1))
    return None


# --- WORKER FUNCTION ---
def process_verification(gen_path: Path, trans_path: Path, output_root: Path, verifier: FactVerifier):
    try:
        model_name = "gpt-5.1" # e.g., "gpt-4.1"
        
        # Setup Output
        target_dir = output_root / model_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        cid = extract_error_number(gen_path.name)
        out_name = f"error_{cid}.json"
        out_path = target_dir / out_name
        
        if not OVERWRITE and out_path.exists():
            return "Skipped"

        # Load Data
        with open(trans_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
            
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
            "model_source": gen_data.get("model_source"),
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

def compare_facts(erroneous=False):
    BASE_PATH = Path(__file__).resolve().parents[1]  
    # points to Reducing-Hallucinations-in-Clinical-Diagnosis/

    GEN_ROOT = BASE_PATH / "detectionAG/output/erroneous_note_facts"
    TRANS_DIR = BASE_PATH / "detectionAG/output/erroneous_transcripts"
    OUTPUT_ROOT = BASE_PATH / "detectionAG/output/erroneous_notes_vs_transcript"

    all_tasks = []

    if not erroneous:
    # 1. Index Transcripts
        print(f"Indexing Transcripts...")
        trans_index = {}
        try:
            # Assuming transcripts are named like "day1_consultation01.txt"
            for p in TRANS_DIR.glob("*.txt"):
                cid = extract_consultation_id(p.name)
                if cid:
                    trans_index[cid] = p
        except Exception as e:
            print(f"Error reading Transcript Directory: {e}")
            exit()
        print(f"Found {len(trans_index)} Transcripts.")

        # 2. Gather Tasks
        print("Gathering generated fact files...")
        
        for gen_path in GEN_ROOT.rglob("*.json"):
            cid = extract_consultation_id(gen_path.name)
            
            # Link Gen Fact -> Transcript
            if cid and cid in trans_index:
                trans_path = trans_index[cid]
                all_tasks.append((gen_path, trans_path))
    
    else:
        trans_index = {}  # number -> transcript path

        for p in TRANS_DIR.glob("*.txt"):
            error_num = extract_error_number(p.name)
            if error_num is not None:
                trans_index[error_num] = p
                print("Transcript indexed:", error_num, "->", p.name)

        print(f'Found {len(trans_index)} erroneous Transcripts.')
        x = 0
        for gen_path in GEN_ROOT.rglob("*.json"):
            error_num = extract_error_number(gen_path.name)
            x += 1
            if error_num is not None and error_num in trans_index:
                trans_path = trans_index[error_num]
                all_tasks.append((gen_path, trans_path))
                print(f"Linked: {gen_path.name} <-> {trans_path.name}")
        print("found", x, "generated fact files.")
                
    random.shuffle(all_tasks)
    print(f"Found {len(all_tasks)} pairs to verify.")
    
    # 3. Run
    verifier = FactVerifier(model=VERIFIER_MODEL)
    stats_counter = {"Success": 0, "Skipped": 0, "Error": 0}

    for gen_path, trans_path in tqdm(all_tasks[5:]):
        status = process_verification(gen_path, trans_path, OUTPUT_ROOT, verifier)
        
        if status == "Success": stats_counter["Success"] += 1
        elif status == "Skipped": stats_counter["Skipped"] += 1
        else: 
            stats_counter["Error"] += 1
            print(f"Failed {gen_path.name}: {status}")

    print(f"\nDone. Stats: {stats_counter}")

# --- MAIN ---
if __name__ == "__main__":
    compare_facts(erroneous=True)