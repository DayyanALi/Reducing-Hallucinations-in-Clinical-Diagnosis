# import os
# import glob
# import json
# import time
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# # Import your custom modules
# from configs.fact_extract_prompt import * 
# from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES
# from classes import SoapGenerator, FactExtractor, SoapEvaluator

# # ---------------- CONFIGURATION ---------------- #
# load_dotenv()

# # --- TEST MODE SETTINGS ---
# TEST_MODE = False
# NUM_TEST_FILES = 10

# # --- PATHS (Fixed for Windows) ---
# # Use r"" for raw strings to handle backslashes correctly
# TRANSCRIPT_DIR = "../data/babylon_data/babylonhealth primock57 main transcripts combined"
# GOLD_FACTS_DIR = "../data/babylon_data/babylon_notes_facts"
# BASE_OUTPUT_DIR = "results/rq1_verification"

# REASONING_EFFORT = "medium"  # Options: "low", "medium", "high"
# MODELS_TO_RUN = ["gpt-5"]

# # ---------------- HELPER FUNCTIONS ---------------- #

# def clean_json_text(text):
#     """
#     Cleans LLM output to ensure it is valid JSON.
#     Removes markdown code blocks (```json ... ```).
#     """
#     if not text: return None
#     # Remove markdown code blocks
#     text = text.replace("```json", "").replace("```", "").strip()
#     return text

# def safe_load_json(text, context=""):
#     """
#     Safely loads JSON and prints the raw text if it fails.
#     """
#     cleaned = clean_json_text(text)
#     print(cleaned)

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError as e:
#         print(f"\n❌ JSON PARSING FAILED [{context}]")
#         print(f"   Error: {e}")
#         print(f"   Snippet of raw text: {cleaned[:200]}...") # Print first 200 chars to debug
#         return None

# # ---------------- MAIN ---------------- #

# def main():
#     # Print Absolute Output Path so you know where files are
#     abs_output_path = os.path.abspath(BASE_OUTPUT_DIR)
#     print(f"\n📂 OUTPUTS WILL BE SAVED TO:\n   {abs_output_path}\n")

#     # Setup Output Dirs
#     for model in MODELS_TO_RUN:
#         if REASONING_EFFORT is not None:
#             model_name = model + "_" + REASONING_EFFORT
#         else:
#             model_name = model
#         os.makedirs(os.path.join(BASE_OUTPUT_DIR, model_name, "notes"), exist_ok=True)
#         os.makedirs(os.path.join(BASE_OUTPUT_DIR, model_name, "evaluations"), exist_ok=True)

#     # Get Input Files
#     transcripts = sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt")))
    
#     if TEST_MODE:
#         print(f"⚠️  TEST MODE ACTIVE: Limiting run to first {NUM_TEST_FILES} files.")
#         transcripts = transcripts[:NUM_TEST_FILES]
    
#     print(f"Found {len(transcripts)} transcripts to process.")

#     for model_name in MODELS_TO_RUN:
#         print(f"\n{'='*40}")
#         print(f">>> PROCESSING MODEL: {model_name}")
#         print(f"{'='*40}")
        
#         generator = SoapGenerator(model_name, REASONING_EFFORT)
#         extractor = FactExtractor()
#         evaluator = SoapEvaluator()

#         if REASONING_EFFORT is not None:
#             model_name = model_name + "_" + REASONING_EFFORT
#         for idx, t_file in enumerate(transcripts, 1):
#             base_name = os.path.splitext(os.path.basename(t_file))[0]
#             print(f"\n[{idx}/{len(transcripts)}] Processing: {base_name}")

#             note_path = os.path.join(BASE_OUTPUT_DIR, model_name, "notes", f"{base_name}.json")
#             eval_path = os.path.join(BASE_OUTPUT_DIR, model_name, "evaluations", f"{base_name}_report.json")
            
#             # 1. LOAD TRANSCRIPT & GOLD FACTS
#             try:
#                 with open(t_file, 'r', encoding='utf-8') as f: transcript_text = f.read()
#             except Exception as e:
#                 print(f"   ❌ Error reading transcript: {e}")
#                 continue
            
#             # --- FIX STARTS HERE ---
#             # Try exact match first
#             gold_path = os.path.join(GOLD_FACTS_DIR, f"{base_name}.json")
            
#             # If exact match doesn't exist, try with '_facts' suffix
#             if not os.path.exists(gold_path):
#                 gold_path_alt = os.path.join(GOLD_FACTS_DIR, f"{base_name}_facts.json")
#                 if os.path.exists(gold_path_alt):
#                     gold_path = gold_path_alt
#                 else:
#                     print(f"   ⚠️  Skipping: Gold Facts not found at {gold_path} OR {gold_path_alt}")
#                     continue

#             try:
#                 with open(gold_path, 'r', encoding='utf-8') as f: 
#                     gold_facts = json.load(f)
#             except Exception as e:
#                 print(f"   ❌ Error reading Gold Facts JSON: {e}")
#                 continue
#             # 2. GET GENERATED NOTE
#             gen_note_json = None
            
#             if os.path.exists(note_path): # Check if exists first
#                 # Check if file is empty
#                 if os.path.getsize(note_path) > 0:
#                     with open(note_path, 'r', encoding='utf-8') as f: 
#                         gen_note_json = json.load(f)
#                     print(f"   [Load] Loaded existing note.")
#                 else:
#                     print(f"   [Gen] Existing note was empty. Re-generating...")

#             if not gen_note_json:
#                 print(f"   [Gen] Generating new note...")
#                 try:
#                     # A. Generate Raw Text
#                     raw_note_text = generator.generate(transcript_text)
                    
#                     # B. Extract/Convert to QNOTE JSON (using safe loader)
#                     # Note: We pass raw_note_text to extractor.to_qnote
#                     # Ensure extractor.to_qnote returns a DICT, not a string.
#                     # If extractor returns a string, we parse it here:
#                     temp_extracted = extractor.to_qnote(raw_note_text)
                    
#                     if isinstance(temp_extracted, str):
#                         gen_note_json = safe_load_json(temp_extracted, context="Extraction")
#                     else:
#                         gen_note_json = temp_extracted

#                     if not gen_note_json:
#                         print("   ❌ Generation failed (Invalid JSON output). Skipping evaluation.")
#                         continue
                    
#                     # Save the Note
#                     with open(note_path, 'w', encoding='utf-8') as f:
#                         json.dump(gen_note_json, f, indent=2)
                        
#                 except Exception as e:
#                     print(f"   ❌ Error generating note: {e}")
#                     continue

#             # 3. RUN EVALUATION PIPELINE
#             if os.path.exists(eval_path) and os.path.getsize(eval_path) > 0:
#                 print(f"   [Eval] Report exists, skipping.")
#                 continue

#             print(f"   [Eval] Running Triangulated Evaluation...")
#             try:
#                 # The evaluator likely returns a DICT. If it returns string, we must parse.
#                 raw_report = evaluator.run_pipeline(transcript_text, gold_facts, gen_note_json)
#                 print(raw_report)
#                 print("First")
                
#                 if isinstance(raw_report, str):
#                     report = safe_load_json(raw_report, context="Evaluation")
#                 else:
#                     report = raw_report
#                 print("Second")
#                 if report:
#                     with open(eval_path, 'w', encoding='utf-8') as f:
#                         json.dump(report, f, indent=2)
#                     print(f"   ✅ Report saved.")
#                 else:
#                     print(f"   ❌ Evaluation produced invalid JSON.")
                
#             except Exception as e:
#                 print(f"   ❌ Error evaluating: {e}")

#             time.sleep(0.5)

#     print("\n>>> TEST RUN COMPLETE.")

# if __name__ == "__main__":
#     main()




import os
import glob
import json
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# --- PATHS ---
TRANSCRIPT_DIR = "../data/babylon_data/babylonhealth primock57 main transcripts combined"
GOLD_FACTS_DIR = "../data/babylon_data/babylon_notes_facts"
BASE_OUTPUT_DIR = "results/rq1_verification"

REASONING_EFFORT = None  # low | medium | high
MODELS_TO_RUN = ["gpt-5.2"]

# --- THREADING ---
MAX_WORKERS = 4  # 3–5 recommended for API stability

# ---------------- HELPER FUNCTIONS ---------------- #

def clean_json_text(text):
    if not text:
        return None
    return text.replace("```json", "").replace("```", "").strip()

def safe_load_json(text, context=""):
    cleaned = clean_json_text(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON PARSING FAILED [{context}]")
        print(f"   Error: {e}")
        print(f"   Snippet: {cleaned[:200]}...")
        return None

# ---------------- WORKER FUNCTION ---------------- #

def process_single_transcript(
    idx,
    total,
    t_file,
    model_name,
    generator,
    extractor,
    evaluator
):
    base_name = os.path.splitext(os.path.basename(t_file))[0]
    print(f"\n[{idx}/{total}] Processing: {base_name}")

    note_path = os.path.join(BASE_OUTPUT_DIR, model_name, "notes", f"{base_name}.json")
    eval_path = os.path.join(BASE_OUTPUT_DIR, model_name, "evaluations", f"{base_name}_report.json")

    # 1. LOAD TRANSCRIPT
    try:
        with open(t_file, "r", encoding="utf-8") as f:
            transcript_text = f.read()
    except Exception as e:
        print(f"   ❌ Error reading transcript: {e}")
        return

    # 2. LOAD GOLD FACTS
    gold_path = os.path.join(GOLD_FACTS_DIR, f"{base_name}.json")
    if not os.path.exists(gold_path):
        gold_path_alt = os.path.join(GOLD_FACTS_DIR, f"{base_name}_facts.json")
        if os.path.exists(gold_path_alt):
            gold_path = gold_path_alt
        else:
            print(f"   ⚠️  Gold facts not found for {base_name}")
            return

    try:
        with open(gold_path, "r", encoding="utf-8") as f:
            gold_facts = json.load(f)
    except Exception as e:
        print(f"   ❌ Error reading gold facts: {e}")
        return

    # 3. LOAD OR GENERATE NOTE
    gen_note_json = None

    if os.path.exists(note_path) and os.path.getsize(note_path) > 0:
        with open(note_path, "r", encoding="utf-8") as f:
            gen_note_json = json.load(f)
        print("   [Load] Loaded existing note.")
    else:
        print("   [Gen] Generating new note...")
        try:
            raw_note_text = generator.generate(transcript_text)
            extracted = extractor.to_qnote(raw_note_text)

            if isinstance(extracted, str):
                gen_note_json = safe_load_json(extracted, context="Extraction")
            else:
                gen_note_json = extracted

            if not gen_note_json:
                print("   ❌ Invalid generated JSON.")
                return

            with open(note_path, "w", encoding="utf-8") as f:
                json.dump(gen_note_json, f, indent=2)

        except Exception as e:
            print(f"   ❌ Error generating note: {e}")
            return

    # 4. EVALUATION
    if os.path.exists(eval_path) and os.path.getsize(eval_path) > 0:
        print("   [Eval] Report exists, skipping.")
        return

    print("   [Eval] Running Triangulated Evaluation...")
    try:
        raw_report = evaluator.run_pipeline(
            transcript_text,
            gold_facts,
            gen_note_json
        )

        if isinstance(raw_report, str):
            report = safe_load_json(raw_report, context="Evaluation")
        else:
            report = raw_report

        if report:
            with open(eval_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print("   ✅ Report saved.")
        else:
            print("   ❌ Invalid evaluation JSON.")

    except Exception as e:
        print(f"   ❌ Error during evaluation: {e}")

    # Keep original throttling behavior
    time.sleep(0.5)

# ---------------- MAIN ---------------- #

def main():
    abs_output_path = os.path.abspath(BASE_OUTPUT_DIR)
    print(f"\n📂 OUTPUTS WILL BE SAVED TO:\n   {abs_output_path}\n")

    # Setup directories
    for model in MODELS_TO_RUN:
        suffix = f"{model}_{REASONING_EFFORT}" if REASONING_EFFORT else model
        os.makedirs(os.path.join(BASE_OUTPUT_DIR, suffix, "notes"), exist_ok=True)
        os.makedirs(os.path.join(BASE_OUTPUT_DIR, suffix, "evaluations"), exist_ok=True)

    transcripts = sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt")))

    if TEST_MODE:
        print(f"⚠️  TEST MODE: Limiting to {NUM_TEST_FILES} files.")
        transcripts = transcripts[:NUM_TEST_FILES]

    print(f"Found {len(transcripts)} transcripts.")

    for model in MODELS_TO_RUN:
        print(f"\n{'='*40}")
        print(f">>> PROCESSING MODEL: {model}")
        print(f"{'='*40}")

        generator = SoapGenerator(model, REASONING_EFFORT)
        extractor = FactExtractor()
        evaluator = SoapEvaluator()

        model_name = f"{model}_{REASONING_EFFORT}" if REASONING_EFFORT else model

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []

            for idx, t_file in enumerate(transcripts, 1):
                futures.append(
                    executor.submit(
                        process_single_transcript,
                        idx,
                        len(transcripts),
                        t_file,
                        model_name,
                        generator,
                        extractor,
                        evaluator
                    )
                )

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"   ❌ Thread crashed: {e}")

    print("\n>>> RUN COMPLETE.")

if __name__ == "__main__":
    main()
