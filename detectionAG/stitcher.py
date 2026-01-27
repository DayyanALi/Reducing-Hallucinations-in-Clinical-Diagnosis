import os
import json
import glob

# ---------------- CONFIGURATION ---------------- #
MODEL_NAME = "gpt-5-nano"

# Your Paths (Unchanged as requested)
PATHS = {
    "transcript": r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\data\babylon_data\babylonhealth primock57 main transcripts combined",
    "gold_facts": r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\data\babylon_data\babylon_notes_facts",
    "gen_note":   r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\detectionAG\detectionAGJust5.1\results\rq1_verification\gpt-5-nano\notes",
    "evaluation": r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\detectionAG\detectionAGJust5.1\results\rq1_verification\gpt-5-nano\evaluations"
}

OUTPUT_DIR = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\detectionAG\results\master_views_Not4O"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- HELPER ---------------- #
def load_file(path, is_json=True):
    if not os.path.exists(path):
        return f"MISSING FILE: {path}"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f) if is_json else f.read()
    except Exception as e:
        return f"ERROR READING: {e}"

# ---------------- MAIN ---------------- #
def main():
    # 1. Find all generated notes to process
    search_pattern = os.path.join(PATHS["gen_note"], "*.json")
    note_files = sorted(glob.glob(search_pattern))
    
    if not note_files:
        print(f"❌ No generated notes found in: {PATHS['gen_note']}")
        return

    print(f"Found {len(note_files)} notes. Generating Master Views...\n")

    for idx, note_path in enumerate(note_files, 1):
        # Extract base name (e.g., "day1_consultation02")
        base_name = os.path.splitext(os.path.basename(note_path))[0]
        
        print(f"[{idx}/{len(note_files)}] Processing: {base_name}...")

        # 2. Define file paths for this specific patient
        files = {
            "1_transcript": os.path.join(PATHS["transcript"], f"{base_name}.txt"),
            "2_gold_facts": os.path.join(PATHS["gold_facts"], f"{base_name}.json"),
            "3_generated_note": note_path, # We already have this path
            "4_evaluation_report": os.path.join(PATHS["evaluation"], f"{base_name}_report.json")
        }

        # 3. Load Data
        master_data = {
            "metadata": {
                "patient_id": base_name,
                "model": MODEL_NAME
            },
            "TRANSCRIPT (The Truth)": load_file(files["1_transcript"], is_json=False),
            "GOLD_FACTS (Human Baseline)": load_file(files["2_gold_facts"], is_json=True),
            "GENERATED_NOTE (AI Output)": load_file(files["3_generated_note"], is_json=True),
            "EVALUATION_REPORT (The Verdict)": load_file(files["4_evaluation_report"], is_json=True)
        }

        # 4. Save Master Report
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}_MASTER.json")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(master_data, f, indent=4)
        except Exception as e:
            print(f"   ❌ Failed to save master file: {e}")

    print(f"\n✅ ALL DONE! Master views saved to:\n   {OUTPUT_DIR}")

if __name__ == "__main__":
    main()