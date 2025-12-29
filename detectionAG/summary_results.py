import json
import pandas as pd
from pathlib import Path

# --- CONFIGURATION ---
# We point to the parent folder containing all model subfolders
BASE_DIR = Path(".") 
RESULTS_DIR = BASE_DIR / "output/comparisons_set1" 

OUTPUT_CSV_METRICS = "analysis_metrics.csv"
OUTPUT_CSV_ERRORS = "analysis_errors.csv"

def parse_results():
    metrics_data = []
    errors_data = []

    # Verify directory exists
    if not RESULTS_DIR.exists():
        print(f"CRITICAL ERROR: Directory not found: {RESULTS_DIR.resolve()}")
        return

    # Recursive search: Finds all .json files in comparisons/gpt-4.1/, comparisons/gpt-4o/, etc.
    json_files = list(RESULTS_DIR.rglob("*.json"))
    
    if not json_files:
        print("No JSON files found. Check your path.")
        return

    print(f"Found {len(json_files)} evaluation files. Processing...")

    for fpath in json_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Intelligent Model Name Extraction
            # 1. Try getting it from JSON
            model = data.get("model_source")
            # 2. If missing, grab it from the parent folder name (e.g., 'gpt-4.1')
            if not model:
                model = fpath.parent.name
            
            file_id = data.get("file_id", fpath.stem)
            
            # --- 1. Harvest High-Level Metrics (One row per file) ---
            m = data.get("metrics", {})
            if m: # Only process if metrics exist
                metrics_row = {
                    "model": model,
                    "file_id": file_id,
                    "total_gold_facts": m.get("total_gold_facts"),
                    "total_gen_facts": m.get("total_gen_facts"),
                    "omission_rate": m.get("omission_rate"),
                    "contradiction_rate": m.get("contradiction_rate"),
                    "addition_rate": m.get("addition_rate"),
                    # Calculate a simple "Total Error Score"
                    "total_error_score": (m.get("omission_rate", 0) or 0) + 
                                         (m.get("contradiction_rate", 0) or 0) + 
                                         (m.get("addition_rate", 0) or 0)
                }
                metrics_data.append(metrics_row)

            # --- 2. Harvest Detailed Errors (One row per specific error) ---
            raw_asm = data.get("raw_assessment", {})
            
            # A. Check Gold Assessment (Look for OMISSIONS)
            for item in raw_asm.get("gold_assessment", []):
                status = item.get("status", "UNKNOWN")
                if status != "COVERED": 
                    errors_data.append({
                        "model": model,
                        "file_id": file_id,
                        "error_category": "OMISSION", # It was in Gold, but not Covered
                        "detailed_type": status,      # e.g., OMITTED or CONTRADICTION
                        "section": item.get("fact_id", "unknown").split("-")[0],
                        "reasoning": item.get("reasoning", "")
                    })

            # B. Check Gen Assessment (Look for ADDITIONS / CONTRADICTIONS)
            for item in raw_asm.get("gen_assessment", []):
                status = item.get("status", "UNKNOWN")
                if status not in ["SUPPORTED", "NEUTRAL"]:
                    errors_data.append({
                        "model": model,
                        "file_id": file_id,
                        "error_category": "HALLUCINATION", # It wasn't in Gold
                        "detailed_type": status,           # e.g., ADDITION or CONTRADICTION
                        "section": item.get("fact_id", "unknown").split("-")[0],
                        "reasoning": item.get("reasoning", "")
                    })

        except Exception as e:
            print(f"Skipping {fpath.name}: {e}")

    # --- Save to CSV ---
    if metrics_data:
        df_metrics = pd.DataFrame(metrics_data)
        df_metrics.to_csv(OUTPUT_CSV_METRICS, index=False)
        print(f"SUCCESS: Saved {len(df_metrics)} rows to '{OUTPUT_CSV_METRICS}'")
    else:
        print("WARNING: No metric data extracted.")

    if errors_data:
        df_errors = pd.DataFrame(errors_data)
        df_errors.to_csv(OUTPUT_CSV_ERRORS, index=False)
        print(f"SUCCESS: Saved {len(df_errors)} detailed errors to '{OUTPUT_CSV_ERRORS}'")
    else:
        print("WARNING: No error data extracted.")

if __name__ == "__main__":
    parse_results()