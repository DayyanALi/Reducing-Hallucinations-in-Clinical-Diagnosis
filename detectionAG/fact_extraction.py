import os
import json
import re
import random
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import concurrent.futures
from tqdm import tqdm

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from configs.fact_extract_prompt import * # Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
OVERWRITE = True  # Set to True to re-process files even if they already exist

# --- 2. The Extraction Agent ---

class FactExtractor:
    def __init__(self, model: str = "gpt-5.1"): 
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
        
        # Invoke Chain
        chain = prompt | self.llm | self.parser
        try:
            qnote_json = chain.invoke({"note_text": note_text})
            return self._flatten_qnote_to_list(qnote_json)
            
        except Exception as e:
            # Simple error logging that won't break the thread
            return [{"error": str(e)}]

    def _flatten_qnote_to_list(self, qnote_json: Dict) -> List[Dict[str, str]]:
        flat_facts = []
        # Handle cases where parsing failed entirely
        if not isinstance(qnote_json, dict):
            return []
            
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

# --- 3. The Worker Function ---

def process_single_file(note_path: Path, extractor: FactExtractor, out_dir: Path, root_notes_dir: Path):
    """
    Runs inside a single thread.
    root_notes_dir: The base folder (reasoning_notes) used to calculate relative paths.
    """
    try:
        # --- PATH FIX ---
        # Calculate path relative to "reasoning_notes"
        # If path is: .../reasoning_notes/gpt-5_high/note.txt
        # relative is: gpt-5_high/note.txt
        relative_path = note_path.relative_to(root_notes_dir)
        
        # The first part of the relative path is your model folder (gpt-5_high)
        model_folder_name = relative_path.parts[0]
        
        # Create output directory: .../extracted_facts/gpt-5_high
        target_dir = out_dir / model_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        out_name = f"facts_{note_path.stem}.json"
        out_path = target_dir / out_name
        
        if not OVERWRITE and out_path.exists():
             return f"Skipped (Exists): {note_path.name}"
        
        # Read
        with open(note_path, "r", encoding="utf-8") as f:
            note_text = f.read()

        # Extract
        facts_list = extractor.extract_facts(note_text)
        
        # Write
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "source_file": note_path.name,
                "model_source": str(model_folder_name),
                "fact_count": len(facts_list),
                "facts": facts_list
            }, f, indent=2, ensure_ascii=False)
            
        return f"Success: {note_path.name}"
        
    except Exception as e:
        return f"Failed: {note_path.name} | Error: {str(e)}"

# --- 4. Execution Main ---
if __name__ == "__main__":
    # Use absolute path if you are unsure where you are running the script from
    # Or keep relative if you run this from the 'detectionAG' folder
    BASE_DIR = Path(".") 
    
    # Ensure this matches your actual folder structure
    NOTES_DIR = BASE_DIR / "experiements/reasoning_notes"
    OUT_DIR = BASE_DIR / "experiements/extracted_facts_reasoning"
    
    print(f"Scanning: {NOTES_DIR.resolve()}")

    try:
        # Get all text files recursively
        all_files = sorted([p for p in NOTES_DIR.rglob("*.txt")])
        
        # --- FILTERING LOGIC (UPDATED) ---
        # Exclude files in 'gpt-4.1' folder
        note_files = []
        for p in all_files:
            try:
                # Check the top-level folder name inside NOTES_DIR
                folder_name = p.relative_to(NOTES_DIR).parts[0]
                if folder_name != "gpt-4.1":
                    note_files.append(p)
            except ValueError:
                # Should not happen if p is inside NOTES_DIR
                continue
        
    except Exception as e:
        print(f"Error reading directory {NOTES_DIR}: {e}")
        note_files = []

    if not note_files:
        print(f"No notes found in {NOTES_DIR}. Check your path.")
        exit()

    files_to_process = note_files # Set slice [:5] here for testing
    random.shuffle(files_to_process)

    print(f"Found {len(all_files)} total files.")
    print(f"Processing {len(files_to_process)} files...")
    
    # Initialize Extractor
    extractor = FactExtractor(model="gpt-4o") # Verify model name

    MAX_WORKERS = 5
    
    print(f"Starting parallel extraction with {MAX_WORKERS} threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Pass NOTES_DIR as the new 4th argument
        futures = {
            executor.submit(process_single_file, file_path, extractor, OUT_DIR, NOTES_DIR): file_path 
            for file_path in files_to_process
        }
        
        stats = {"Success": 0, "Skipped": 0, "Failed": 0}

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(files_to_process)):
            file_path = futures[future]
            try:
                result = future.result()
                
                if "Success" in result: stats["Success"] += 1
                elif "Skipped" in result: stats["Skipped"] += 1
                elif "Failed" in result: stats["Failed"] += 1
                
                if "Skipped" not in result:
                    tqdm.write(result)
                    
            except Exception as exc:
                stats["Failed"] += 1
                print(f'{file_path.name} generated an exception: {exc}')

    print(f"\nDone. Extracted facts saved to: {OUT_DIR}")
    print(f"Summary: {stats}")