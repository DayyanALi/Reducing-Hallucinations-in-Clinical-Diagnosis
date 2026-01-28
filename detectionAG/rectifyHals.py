import os
import json
import glob
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from configs.fact_extract_prompt import PHASE2_SYSTEM

# ---------------- CONFIGURATION ---------------- #
load_dotenv()

# Path to your current results
BASE_OUTPUT_DIR = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\detectionAG\detectionAGJust5.1\results\rq1_verification"
TRANSCRIPT_DIR = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\data\babylon_data\babylonhealth primock57 main transcripts combined"

# Which models to fix?
MODELS_TO_FIX = ["gpt-5-nano", "gpt-4o","gpt-4.1-mini","gpt-4.1","gpt-5","gpt-5-mini"] 

# ---------------- THE FIXED PHASE 2 PROMPT ---------------- #
# ---------------- HELPER FUNCTIONS ---------------- #

def normalize_id(f_id):
    """
    Fixes the 'Leading Zero' bug.
    Example: 'Plan_of_Care-005' -> 'Plan_of_Care-5'
    Example: 'hpi-01' -> 'hpi-1'
    """
    if not f_id or '-' not in f_id:
        return f_id
    
    parts = f_id.rsplit('-', 1)
    prefix = parts[0]
    number = parts[1]
    
    if number.isdigit():
        return f"{prefix}-{int(number)}"
    return f_id

def load_json_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def flatten_facts(note_json):
    """
    Turns the nested Q-Note JSON (Medications: [...]) into a single flat map
    ID -> Content for easy lookup.
    """
    flat_map = {}
    for category, items in note_json.items():
        if isinstance(items, list):
            for item in items:
                f_id = item.get("fact_id")
                content = item.get("content", "").strip()
                if f_id:
                    flat_map[normalize_id(f_id)] = content
    return flat_map

# ---------------- MAIN LOGIC ---------------- #

def main():
    llm = ChatOpenAI(model="gpt-4o", temperature=0) # Use your best model for verification
    parser = JsonOutputParser()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PHASE2_SYSTEM),
        ("human", "Transcript:\n{transcript}\n\nFacts to Verify:\n{facts}")
    ])
    
    chain = prompt | llm | parser

    for model in MODELS_TO_FIX:
        print(f"\n{'='*40}")
        print(f">>> RE-VERIFYING MODEL: {model}")
        print(f"{'='*40}")

        eval_dir = os.path.join(BASE_OUTPUT_DIR, model, "evaluations")
        note_dir = os.path.join(BASE_OUTPUT_DIR, model, "notes")
        
        if not os.path.exists(eval_dir): continue

        json_files = glob.glob(os.path.join(eval_dir, "*.json"))

        for idx, report_path in enumerate(json_files, 1):
            filename = os.path.basename(report_path)
            base_name = filename.replace("_report.json", "") # e.g. day1_consultation01
            
            print(f"[{idx}/{len(json_files)}] Fixing: {base_name}")

            # 1. Load Data
            report_data = load_json_safe(report_path)
            note_data = load_json_safe(os.path.join(note_dir, f"{base_name}.json"))
            
            # Find Transcript
            transcript_path = os.path.join(TRANSCRIPT_DIR, f"{base_name}.txt")
            if not os.path.exists(transcript_path):
                print(f"   ⚠️ Transcript not found. Skipping.")
                continue
                
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            if not report_data or not note_data:
                print("   ⚠️ Missing report or note file. Skipping.")
                continue

            # 2. Build Content Map (Normalized)
            content_map = flatten_facts(note_data)

            # 3. Identify Facts Needing Verification
            # We look for 'NOT_IN_GOLD' in the existing report
            facts_to_verify = []
            gen_assessment = report_data.get("gen_assessment", [])
            
            # Create a lookup for the report items so we can update them in place
            report_item_map = {item.get("fact_id"): item for item in gen_assessment}

            for item in gen_assessment:
                if item.get("status") == "NOT_IN_GOLD":
                    raw_id = item.get("fact_id")
                    norm_id = normalize_id(raw_id)
                    
                    # RETRIEVE CONTENT
                    content = content_map.get(norm_id)
                    
                    # --- GHOST FACT CHECK ---
                    if not content or len(content) < 3:
                        # It's a ghost! Mark as Schema Error immediately.
                        item["final_status"] = "SCHEMA_ERROR"
                        item["verification_reasoning"] = "Empty or missing content in generated note (Ghost Fact)."
                        continue # Skip LLM
                    
                    # If valid, add to list for LLM
                    facts_to_verify.append({
                        "fact_id": raw_id, # Send raw ID so we can match it back
                        "content": content
                    })

            # 4. Run LLM Batch (if needed)
            if facts_to_verify:
                try:
                    # Run the chain
                    # Note: You might want to batch this if the list is huge, 
                    # but usually it's <20 facts per file.
                    result = chain.invoke({
                        "transcript": transcript_text,
                        "facts": json.dumps(facts_to_verify)
                    })
                    
                    # 5. Merge Results Back
                    # The result should have a "verdict" list
                    verdicts = result.get("verdict", [])
                    if not verdicts and isinstance(result, list): 
                        verdicts = result # Handle case where LLM returns just a list
                        
                    for v in verdicts:
                        f_id = v.get("fact_id")
                        if f_id in report_item_map:
                            report_item_map[f_id]["final_status"] = v.get("status")
                            report_item_map[f_id]["verification_reasoning"] = v.get("reasoning")
                            
                    print(f"   ✅ Re-verified {len(facts_to_verify)} facts.")
                    
                except Exception as e:
                    print(f"   ❌ LLM Error: {e}")
            else:
                print("   Transformation complete (No valid facts to verify).")

            # 6. Save Updates (Overwriting specific fields only)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)

    print("\n>>> RE-VERIFICATION COMPLETE.")

if __name__ == "__main__":
    main()