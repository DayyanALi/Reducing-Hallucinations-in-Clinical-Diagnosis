import os
import json
import re
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from tqdm import tqdm

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import Prompts
from configs.fact_extract_prompt import (
    FACT_EXTRACT_SYSTEM_PROMPT, 
    FACT_NEW_USER_PROMPT,
    FACT_VERIFY_SYSTEM_PROMPT, 
    FACT_VERIFY_USER_PROMPT
)

load_dotenv()

# --- CONFIGURATION ---
EXTRACTOR_MODEL = "gpt-5.1"  
VERIFIER_MODEL = "gpt-5.1"   
OVERWRITE = False            # Set False to skip files you already processed
MAX_WORKERS = 3              # 3-4 threads as requested

# ==========================================
# PART 1: CLASSES
# ==========================================

class FactExtractor:
    def __init__(self, model: str = EXTRACTOR_MODEL): 
        self.llm = ChatOpenAI(
            model=model,  
            model_kwargs={"response_format": {"type": "json_object"}},
            max_retries=5 
        )
        self.parser = JsonOutputParser()

    def extract_facts(self, note_text: str) -> List[Dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", FACT_EXTRACT_SYSTEM_PROMPT),
            ("user", FACT_NEW_USER_PROMPT),
        ])
        chain = prompt | self.llm | self.parser
        try:
            qnote_json = chain.invoke({"note_text": note_text})
            return self._flatten_qnote_to_list(qnote_json)
        except Exception as e:
            return [{"error": str(e)}]

    def _flatten_qnote_to_list(self, qnote_json: Dict) -> List[Dict[str, str]]:
        flat_facts = []
        if not isinstance(qnote_json, dict): return []
        for section, facts_list in qnote_json.items():
            if isinstance(facts_list, list):
                for fact in facts_list:
                    flat_facts.append({
                        "id": fact.get("fact_id"),
                        "section": section,
                        "content": fact.get("content", "").strip(),
                        "source_text": fact.get("source_text", "")
                    })
        return flat_facts


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
        if not gen_facts: return {"verdict": []}
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", FACT_VERIFY_SYSTEM_PROMPT),
            ("user", FACT_VERIFY_USER_PROMPT),
        ])
        chain = prompt | self.llm | self.parser
        
        try:
            slim_facts = [{"fact_id": f["id"], "content": f["content"]} for f in gen_facts]
            return chain.invoke({
                "transcript": transcript_text,
                "facts_json": json.dumps(slim_facts, indent=1)
            })
        except Exception as e:
            return {"error": str(e), "verdict": []}

# ==========================================
# PART 2: HELPER FUNCTIONS
# ==========================================

def extract_consultation_id(filename: str) -> str:
    match = re.search(r"(day\d+_consultation\d+)", filename)
    if match: return match.group(1)
    return None

def process_full_pipeline_on_file(note_path: Path, trans_path: Path, 
                                  extractor: FactExtractor, verifier: FactVerifier, 
                                  fact_out_root: Path, verify_out_root: Path):
    """
    Runs Extraction -> Saving -> Verification -> Saving for a single file.
    """
    try:
        # --- 1. SETUP PATHS ---
        model_name = note_path.parent.name # e.g. "gpt-4.1"
        cid = extract_consultation_id(note_path.name)
        
        # Output Directories
        fact_dir = fact_out_root / model_name
        fact_dir.mkdir(parents=True, exist_ok=True)
        fact_out_path = fact_dir / f"facts_{note_path.stem}.json"

        verify_dir = verify_out_root / model_name
        verify_dir.mkdir(parents=True, exist_ok=True)
        verify_out_path = verify_dir / f"verification_{cid}.json"

        # Check if Verification already exists (Final step completed)
        if not OVERWRITE and verify_out_path.exists():
            return f"Skipped (Done): {model_name}/{note_path.name}"

        # --- 2. STEP 1: FACT EXTRACTION ---
        if OVERWRITE or not fact_out_path.exists():
            with open(note_path, "r", encoding="utf-8") as f:
                note_text = f.read()
            
            facts_list = extractor.extract_facts(note_text)
            
            if not facts_list or "error" in facts_list[0]:
                 return f"Extraction Failed: {model_name}/{note_path.name}"

            # Save Facts
            with open(fact_out_path, "w", encoding="utf-8") as f:
                json.dump({
                    "source_file": note_path.name,
                    "model_source": str(model_name),
                    "fact_count": len(facts_list),
                    "facts": facts_list
                }, f, indent=2, ensure_ascii=False)
        else:
            # Load existing facts if we are just running verification
            with open(fact_out_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                facts_list = data.get("facts", [])

        # --- 3. STEP 2: VERIFICATION ---
        if OVERWRITE or not verify_out_path.exists():
            with open(trans_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()

            result = verifier.verify_facts(transcript_text, facts_list)

            if "error" in result:
                return f"Verification Error: {result['error']}"

            # Metrics
            stats = {"SUPPORTED": 0, "ADDITION": 0, "CONTRADICTION": 0}
            for v in result.get("verdict", []):
                status = v.get("status", "UNKNOWN")
                if status in stats: stats[status] += 1
            
            total = len(result.get("verdict", []))
            
            final_report = {
                "file_id": note_path.name,
                "model_source": model_name,
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

            with open(verify_out_path, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=2)

        return f"Success: {model_name}/{note_path.name}"

    except Exception as e:
        return f"Failed: {note_path.name} | {str(e)}"

# ==========================================
# PART 3: MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    
    # --- PATHS ---
    BASE_PATH = Path("E:/hallucination/Reducing-Hallucinations-in-Clinical-Diagnosis")
    
    # Inputs
    NOTES_ROOT = BASE_PATH / "detectionAG/output/notes_text"
    TRANS_DIR = BASE_PATH / "detectionAG/output/transcriptions"
    
    # Production Outputs
    OUT_FACTS = BASE_PATH / "detectionAG/output/extracted_facts_set1"
    OUT_VERIFY = BASE_PATH / "detectionAG/output/verifications_vs_transcript"
    
    # --- 1. INDEX TRANSCRIPTS ---
    print("Indexing Transcripts...")
    trans_index = {}
    for p in TRANS_DIR.glob("*.txt"):
        cid = extract_consultation_id(p.name)
        if cid: trans_index[cid] = p
    
    print(f"Found {len(trans_index)} transcripts.")

    # --- 2. GATHER ALL TASKS ---
    print("Gathering all notes from all models...")
    all_tasks = []
    
    # Recursively find all text files in notes_text/ (handles model subfolders)
    # This finds notes_text/gpt-4o/note.txt, notes_text/gpt-5-mini/note.txt, etc.
    note_files = list(NOTES_ROOT.rglob("*.txt"))
    
    for note_path in note_files:
        cid = extract_consultation_id(note_path.name)
        
        if cid and cid in trans_index:
            trans_path = trans_index[cid]
            all_tasks.append((note_path, trans_path))
        else:
            # Optional: Warning for unmatched files
            # print(f"Warning: No transcript for {note_path.name}")
            pass

    print(f"\nQueueing {len(all_tasks)} total tasks across all models.")
    print(f"Workers: {MAX_WORKERS}")
    print(f"Output: {OUT_VERIFY}")

    # --- 3. RUN PARALLEL PIPELINE ---
    extractor = FactExtractor()
    verifier = FactVerifier()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_full_pipeline_on_file, note_path, trans_path, 
                            extractor, verifier, OUT_FACTS, OUT_VERIFY): note_path
            for (note_path, trans_path) in all_tasks
        }

        stats = {"Success": 0, "Skipped": 0, "Failed": 0}
        
        # Using TQDM to show progress bar
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(all_tasks)):
            result = future.result()
            
            if "Success" in result: stats["Success"] += 1
            elif "Skipped" in result: stats["Skipped"] += 1
            else: 
                stats["Failed"] += 1
                tqdm.write(result) # Print errors above the progress bar

    print(f"\n--- Batch Complete ---")
    print(f"Summary: {stats}")