import json
import pandas as pd
from pathlib import Path

# --- CONFIGURATION ---
INPUT_DIR = Path("E:/hallucination/Reducing-Hallucinations-in-Clinical-Diagnosis/detectionAG/output/verifications_vs_transcript")
OUTPUT_METRICS_CSV = "analysis_metrics_summary.csv"
OUTPUT_FACTS_CSV = "analysis_facts_detail.csv"

def harvest_data():
    file_records = []
    fact_records = []

    # Recursively find all verification JSON files
    json_files = list(INPUT_DIR.rglob("*.json"))
    
    print(f"Found {len(json_files)} files. Processing...")

    for fpath in json_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 1. Extract File-Level Metadata
            # Fallback to folder name if model_source is missing in JSON
            model_name = data.get("model_source") or fpath.parent.name
            file_id = data.get("file_id", fpath.name)
            
            metrics = data.get("metrics", {})
            
            file_records.append({
                "model": model_name,
                "file_id": file_id,
                "total_facts": metrics.get("total_facts", 0),
                "supported_count": metrics.get("supported_count", 0),
                "addition_count": metrics.get("addition_count", 0),
                "contradiction_count": metrics.get("contradiction_count", 0),
                "hallucination_rate": metrics.get("hallucination_rate", 0.0)
            })

            # 2. Extract Fact-Level Details
            verdict_list = data.get("verdict", [])
            for item in verdict_list:
                # Extract section from fact_id (e.g., "hpi-001" -> "hpi")
                fact_id = item.get("fact_id", "unknown")
                section_tag = fact_id.split("-")[0] if "-" in fact_id else "unknown"
                
                fact_records.append({
                    "model": model_name,
                    "file_id": file_id,
                    "fact_id": fact_id,
                    "section_tag": section_tag,
                    "status": item.get("status"),
                    "reasoning": item.get("reasoning")
                })

        except Exception as e:
            print(f"Skipping {fpath.name}: {e}")

    # Convert to DataFrames
    df_files = pd.DataFrame(file_records)
    df_facts = pd.DataFrame(fact_records)

    return df_files, df_facts

if __name__ == "__main__":
    df_files, df_facts = harvest_data()
    
    # Save to CSV
    df_files.to_csv(OUTPUT_METRICS_CSV, index=False)
    df_facts.to_csv(OUTPUT_FACTS_CSV, index=False)
    
    print(f"\n--- Processing Complete ---")
    print(f"File Metrics saved to: {OUTPUT_METRICS_CSV} ({len(df_files)} rows)")
    print(f"Fact Details saved to: {OUTPUT_FACTS_CSV} ({len(df_facts)} rows)")
    
    # Optional: Print a quick preview analysis
    if not df_files.empty:
        print("\n--- Quick Leaderboard (Avg Hallucination Rate) ---")
        print(df_files.groupby("model")["hallucination_rate"].mean().sort_values())