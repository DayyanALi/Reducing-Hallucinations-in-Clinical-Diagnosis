import os
import glob
import json
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import your custom modules
from configs.fact_extract_prompt import * 
from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES
from classes import SoapGenerator, FactExtractor, SoapEvaluator

# ---------------- CONFIGURATION ---------------- #
load_dotenv()

# --- TEST MODE SETTINGS ---
TEST_MODE = False
NUM_TEST_FILES = 10

# --- PATHS (Fixed for Windows) ---
# Use r"" for raw strings to handle backslashes correctly
TRANSCRIPT_DIR = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\data\babylon_data\babylonhealth primock57 main transcripts combined"
GOLD_FACTS_DIR = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\data\babylon_data\babylon_notes_facts"
BASE_OUTPUT_DIR = r"detectionAGJust5.1\results\rq1_verification"

MODELS_TO_RUN = ["o3"]

# ---------------- HELPER FUNCTIONS ---------------- #

def clean_json_text(text):
    """
    Cleans LLM output to ensure it is valid JSON.
    Removes markdown code blocks (```json ... ```).
    """
    if not text: return None
    # Remove markdown code blocks
    text = text.replace("```json", "").replace("```", "").strip()
    return text

def safe_load_json(text, context=""):
    """
    Safely loads JSON and prints the raw text if it fails.
    """
    cleaned = clean_json_text(text)
    print(cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON PARSING FAILED [{context}]")
        print(f"   Error: {e}")
        print(f"   Snippet of raw text: {cleaned[:200]}...") # Print first 200 chars to debug
        return None

# ---------------- MAIN ---------------- #

def main():
    # Print Absolute Output Path so you know where files are
    abs_output_path = os.path.abspath(BASE_OUTPUT_DIR)
    print(f"\n📂 OUTPUTS WILL BE SAVED TO:\n   {abs_output_path}\n")

    # Setup Output Dirs
    for model in MODELS_TO_RUN:
        os.makedirs(os.path.join(BASE_OUTPUT_DIR, model, "notes"), exist_ok=True)
        os.makedirs(os.path.join(BASE_OUTPUT_DIR, model, "evaluations"), exist_ok=True)

    # Get Input Files
    transcripts = sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt")))
    
    if TEST_MODE:
        print(f"⚠️  TEST MODE ACTIVE: Limiting run to first {NUM_TEST_FILES} files.")
        transcripts = transcripts[:NUM_TEST_FILES]
    
    print(f"Found {len(transcripts)} transcripts to process.")

    for model_name in MODELS_TO_RUN:
        print(f"\n{'='*40}")
        print(f">>> PROCESSING MODEL: {model_name}")
        print(f"{'='*40}")
        
        generator = SoapGenerator(model_name)
        extractor = FactExtractor()
        evaluator = SoapEvaluator()

        for idx, t_file in enumerate(transcripts, 1):
            base_name = os.path.splitext(os.path.basename(t_file))[0]
            print(f"\n[{idx}/{len(transcripts)}] Processing: {base_name}")
            
            note_path = os.path.join(BASE_OUTPUT_DIR, model_name, "notes", f"{base_name}.json")
            eval_path = os.path.join(BASE_OUTPUT_DIR, model_name, "evaluations", f"{base_name}_report.json")
            
            # 1. LOAD TRANSCRIPT & GOLD FACTS
            try:
                with open(t_file, 'r', encoding='utf-8') as f: transcript_text = f.read()
            except Exception as e:
                print(f"   ❌ Error reading transcript: {e}")
                continue
            
            # --- FIX STARTS HERE ---
            # Try exact match first
            gold_path = os.path.join(GOLD_FACTS_DIR, f"{base_name}.json")
            
            # If exact match doesn't exist, try with '_facts' suffix
            if not os.path.exists(gold_path):
                gold_path_alt = os.path.join(GOLD_FACTS_DIR, f"{base_name}_facts.json")
                if os.path.exists(gold_path_alt):
                    gold_path = gold_path_alt
                else:
                    print(f"   ⚠️  Skipping: Gold Facts not found at {gold_path} OR {gold_path_alt}")
                    continue

            try:
                with open(gold_path, 'r', encoding='utf-8') as f: 
                    gold_facts = json.load(f)
            except Exception as e:
                print(f"   ❌ Error reading Gold Facts JSON: {e}")
                continue
            # 2. GET GENERATED NOTE
            gen_note_json = None
            
            if os.path.exists(note_path): # Check if exists first
                # Check if file is empty
                if os.path.getsize(note_path) > 0:
                    with open(note_path, 'r', encoding='utf-8') as f: 
                        gen_note_json = json.load(f)
                    print(f"   [Load] Loaded existing note.")
                else:
                    print(f"   [Gen] Existing note was empty. Re-generating...")

            if not gen_note_json:
                print(f"   [Gen] Generating new note...")
                try:
                    # A. Generate Raw Text
                    raw_note_text = generator.generate(transcript_text)
                    
                    # B. Extract/Convert to QNOTE JSON (using safe loader)
                    # Note: We pass raw_note_text to extractor.to_qnote
                    # Ensure extractor.to_qnote returns a DICT, not a string.
                    # If extractor returns a string, we parse it here:
                    temp_extracted = extractor.to_qnote(raw_note_text)
                    
                    if isinstance(temp_extracted, str):
                        gen_note_json = safe_load_json(temp_extracted, context="Extraction")
                    else:
                        gen_note_json = temp_extracted

                    if not gen_note_json:
                        print("   ❌ Generation failed (Invalid JSON output). Skipping evaluation.")
                        continue
                    
                    # Save the Note
                    with open(note_path, 'w', encoding='utf-8') as f:
                        json.dump(gen_note_json, f, indent=2)
                        
                except Exception as e:
                    print(f"   ❌ Error generating note: {e}")
                    continue

            # 3. RUN EVALUATION PIPELINE
            if os.path.exists(eval_path) and os.path.getsize(eval_path) > 0:
                print(f"   [Eval] Report exists, skipping.")
                continue

            print(f"   [Eval] Running Triangulated Evaluation...")
            try:
                # The evaluator likely returns a DICT. If it returns string, we must parse.
                raw_report = evaluator.run_pipeline(transcript_text, gold_facts, gen_note_json)
                print(raw_report)
                print("First")
                
                if isinstance(raw_report, str):
                    report = safe_load_json(raw_report, context="Evaluation")
                else:
                    report = raw_report
                print("Second")
                if report:
                    with open(eval_path, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2)
                    print(f"   ✅ Report saved.")
                else:
                    print(f"   ❌ Evaluation produced invalid JSON.")
                
            except Exception as e:
                print(f"   ❌ Error evaluating: {e}")

            time.sleep(0.5)

    print("\n>>> TEST RUN COMPLETE.")

if __name__ == "__main__":
    main()