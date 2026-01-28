import os
import json
import glob
import pandas as pd
import re

# ---------------- CONFIGURATION ---------------- #
BASE_OUTPUT_DIR = r"E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\detectionAG\detectionAGJust5.1\results\rq1_verification"
OUTPUT_FILE = "Research_Paper_Metrics.xlsx"

# ---------------- CATEGORY MAPPING ---------------- #
# This dictionary forces all abbreviations to the standard Q-Note headers.
CATEGORY_MAP = {
    # HPI / Chief Complaint
    "cc": "Chief_Complaint",
    "chief": "Chief_Complaint",
    "chief_complaint": "Chief_Complaint",
    "hpi": "History_of_Present_Illness",
    "history": "History_of_Present_Illness",
    "history_of_present_illness": "History_of_Present_Illness",
    
    # Medical History
    "pmh": "Past_Medical_History",
    "past": "Past_Medical_History",
    "past_medical_history": "Past_Medical_History",
    "psh": "Past_Medical_History",
    
    # Medications & Allergies
    "med": "Medications",
    "meds": "Medications",
    "dh": "Medications",
    "medication": "Medications",
    "medications": "Medications",
    "allergy": "Adverse_Drug_Reactions_and_Allergies",
    "allergies": "Adverse_Drug_Reactions_and_Allergies",
    "adr": "Adverse_Drug_Reactions_and_Allergies",
    "adverse": "Adverse_Drug_Reactions_and_Allergies",
    "adverse_drug_reactions_and_allergies": "Adverse_Drug_Reactions_and_Allergies",
    
    # Family & Social
    "fh": "Family_History",
    "fhx": "Family_History",
    "fam": "Family_History",
    "famhx": "Family_History",
    "family": "Family_History",
    "family_history": "Family_History",
    "sh": "Social_and_Family_History",
    "sfh": "Social_and_Family_History",
    "soc": "Social_and_Family_History",
    "social": "Social_and_Family_History",
    "social_and_family_history": "Social_and_Family_History",
    
    # Assessment & Plan
    "asm": "Assessment",
    "imp": "Assessment",
    "assess": "Assessment",
    "assessment": "Assessment",
    "plan": "Plan_of_Care",
    "mx": "Plan_of_Care",
    "plan_of_care": "Plan_of_Care",
    
    # Follow Up
    "fu": "Follow_up_Information",
    "follow": "Follow_up_Information",
    "follow_up": "Follow_up_Information",
    "follow_up_information": "Follow_up_Information",
    
    # Exam / ROS
    "ros": "Review_of_Systems",
    "review": "Review_of_Systems",
    "review_of_systems": "Review_of_Systems",
    "pe": "Physical_Findings",
    "pf": "Physical_Findings",
    "phys": "Physical_Findings",
    "ex": "Physical_Findings",
    "oe": "Physical_Findings",
    "physical": "Physical_Findings",
    "physical_findings": "Physical_Findings",
    "vitals": "Physical_Findings"
}

def get_category_from_id(fact_id):
    """
    Normalizes fact IDs (e.g. 'hpi-001' or 'History_of_Present_Illness-001')
    into a single consistent category name.
    """
    if not fact_id or not isinstance(fact_id, str):
        return "Unknown"
    
    # 1. Split by hyphen to get the prefix
    # e.g., "hpi-001" -> "hpi"
    # e.g., "History_of_Present_Illness-001" -> "History_of_Present_Illness"
    parts = fact_id.split('-')
    if len(parts) > 0:
        raw_prefix = parts[0].lower().strip()
        
        # 2. Handle cases where underscores are used in generated text
        # e.g. "Adverse_Drug_..." -> split takes the whole thing
        # We check the map first.
        
        # Exact match in map?
        if raw_prefix in CATEGORY_MAP:
            return CATEGORY_MAP[raw_prefix]
        
        # Partial match? (e.g. prefix is "social_anc" -> starts with "social")
        for key in CATEGORY_MAP:
            if raw_prefix.startswith(key):
                return CATEGORY_MAP[key]
                
        # 3. Fallback: If not found, format nicely so it's readable
        return raw_prefix.replace("_", " ").title()
        
    return "Unknown"

# ---------------- ANALYSIS FUNCTIONS ---------------- #

def process_evaluations(base_dir):
    summary_data = []
    hallucination_details = []
    category_data = [] 

    # Find all model directories
    model_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    for model in model_dirs:
        print(f"Processing Model: {model}...")
        
        eval_dir = os.path.join(base_dir, model, "evaluations")
        if not os.path.exists(eval_dir):
            continue

        json_files = glob.glob(os.path.join(eval_dir, "*.json"))

        for file_path in json_files:
            filename = os.path.basename(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

            # --- 1. General File Stats ---
            stats = {
                "Model": model,
                "Filename": filename,
                "Gold_Total": 0, "Gold_Covered": 0, "Gold_Omitted": 0, "Gold_Contradicted": 0,
                "Gen_Total": 0, "Gen_Supported": 0, "Gen_Contradicted": 0,
                "Gen_Valid_Elaboration": 0, "Gen_True_Addition": 0, "Gen_Schema_Error": 0
            }

            # --- 2. Category Tracking (Per File) ---
            cat_tracker = {} 

            def get_cat_bucket(cat_name):
                if cat_name not in cat_tracker:
                    cat_tracker[cat_name] = {
                        "Model": model,
                        "Category": cat_name,
                        "Gen_Total": 0, "Gen_Hallucinations": 0, "Gen_Contradictions": 0, "Gen_Valid_Elabs": 0,
                        "Gold_Total": 0, "Gold_Omissions": 0
                    }
                return cat_tracker[cat_name]

            # --- Process Gold (Recall / Omissions) ---
            if "gold_assessment" in data:
                for item in data["gold_assessment"]:
                    stats["Gold_Total"] += 1
                    status = item.get("status", "UNKNOWN")
                    fact_id = item.get("fact_id")
                    category = get_category_from_id(fact_id)
                    
                    cat_bucket = get_cat_bucket(category)
                    cat_bucket["Gold_Total"] += 1

                    if status == "COVERED":
                        stats["Gold_Covered"] += 1
                    elif status == "OMITTED":
                        stats["Gold_Omitted"] += 1
                        cat_bucket["Gold_Omissions"] += 1
                    elif status == "CONTRADICTED":
                        stats["Gold_Contradicted"] += 1
                        hallucination_details.append({
                            "Model": model,
                            "Filename": filename,
                            "Category": category,
                            "Type": "Gold Contradiction (Factual Error)",
                            "Fact_ID": fact_id,
                            "Reasoning": item.get("reasoning")
                        })

            # --- Process Gen (Precision / Hallucinations) ---
            if "gen_assessment" in data:
                for item in data["gen_assessment"]:
                    stats["Gen_Total"] += 1
                    status = item.get("status", "UNKNOWN")
                    fact_id = item.get("fact_id")
                    category = get_category_from_id(fact_id)
                    
                    cat_bucket = get_cat_bucket(category)
                    cat_bucket["Gen_Total"] += 1

                    if status == "SUPPORTED":
                        stats["Gen_Supported"] += 1
                    
                    elif status == "CONTRADICTED":
                        stats["Gen_Contradicted"] += 1
                        cat_bucket["Gen_Contradictions"] += 1
                        
                        hallucination_details.append({
                            "Model": model,
                            "Filename": filename,
                            "Category": category,
                            "Type": "Generated Contradiction",
                            "Fact_ID": fact_id,
                            "Reasoning": item.get("reasoning")
                        })
                    elif status == "NOT_IN_GOLD":
                        final = item.get("final_status", "UNKNOWN")
                        reasoning = item.get("verification_reasoning", "") or item.get("reasoning", "")
                        
                        # --- FIX: Detect Ghost Facts ---
                        if "CONTENT NOT FOUND" in reasoning or "No specific content" in reasoning:
                             stats["Gen_Schema_Error"] += 1
                             # Do NOT count this as a Hallucination in the Category Bucket
                             # Just skip adding it to cat_bucket["Gen_Hallucinations"]
                        # -------------------------------
                        
                        elif final == "VALID_ELABORATION":
                            stats["Gen_Valid_Elaboration"] += 1
                            cat_bucket["Gen_Valid_Elabs"] += 1
                            
                        elif final == "TRUE_ADDITION":
                            stats["Gen_True_Addition"] += 1
                            cat_bucket["Gen_Hallucinations"] += 1
                            
                            hallucination_details.append({
                                "Model": model,
                                "Filename": filename,
                                "Category": category,
                                "Type": "True Addition (Hallucination)",
                                "Fact_ID": fact_id,
                                "Reasoning": reasoning
                            })

            summary_data.append(stats)
            category_data.extend(list(cat_tracker.values()))

    return summary_data, hallucination_details, category_data

# ---------------- CALCULATIONS & EXPORT ---------------- #

def save_to_excel(summary_data, hallucination_details, category_data, output_file):
    df_summary = pd.DataFrame(summary_data)
    df_details = pd.DataFrame(hallucination_details)
    df_cats = pd.DataFrame(category_data)

    # 1. Model Overview (High Level)
    if not df_summary.empty:
        df_agg = df_summary.groupby("Model").sum(numeric_only=True).reset_index()
        # Metrics
        df_agg["Precision"] = (df_agg["Gen_Supported"] + df_agg["Gen_Valid_Elaboration"]) / df_agg["Gen_Total"]
        df_agg["Recall"] = df_agg["Gold_Covered"] / df_agg["Gold_Total"]
        df_agg["Hallucination_Rate"] = (df_agg["Gen_Contradicted"] + df_agg["Gen_True_Addition"]) / df_agg["Gen_Total"]
    else:
        df_agg = pd.DataFrame()

    # 2. Category Analysis (The "Safety Profile")
    if not df_cats.empty:
        # Group by Model + Category
        df_cat_agg = df_cats.groupby(["Model", "Category"]).sum(numeric_only=True).reset_index()
        
        # Calculate Rates
        df_cat_agg["Hallucination_Rate"] = (df_cat_agg["Gen_Contradictions"] + df_cat_agg["Gen_Hallucinations"]) / df_cat_agg["Gen_Total"]
        df_cat_agg["Omission_Rate"] = df_cat_agg["Gold_Omissions"] / df_cat_agg["Gold_Total"]
        df_cat_agg["Valid_Elab_Ratio"] = df_cat_agg["Gen_Valid_Elabs"] / (df_cat_agg["Gen_Valid_Elabs"] + df_cat_agg["Gen_Hallucinations"])
        
        # Clean up columns for readability
        df_cat_agg = df_cat_agg.fillna(0)
    else:
        df_cat_agg = pd.DataFrame()

    # 3. Qualitative Analysis (Reasoning Keywords)
    if not df_details.empty:
        # Simple keyword tagging
        df_details['Is_Time_Error'] = df_details['Reasoning'].str.contains(r'date|time|duration|year|month|week|day', case=False, na=False)
        df_details['Is_Negation_Error'] = df_details['Reasoning'].str.contains(r'denies|no |not |never|negative', case=False, na=False)
        df_details['Is_Dose_Error'] = df_details['Reasoning'].str.contains(r'dose|mg|amount', case=False, na=False)

    # Write to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_agg.to_excel(writer, sheet_name="Model_Overview", index=False)
        df_cat_agg.to_excel(writer, sheet_name="Category_Analysis", index=False)
        df_details.to_excel(writer, sheet_name="Hallucination_Log", index=False)
        df_summary.to_excel(writer, sheet_name="File_Raw_Data", index=False)
    
    print(f"\n✅ Analysis Complete! Saved to: {os.path.abspath(output_file)}")

# ---------------- RUNNER ---------------- #

if __name__ == "__main__":
    if os.path.exists(BASE_OUTPUT_DIR):
        raw, details, cats = process_evaluations(BASE_OUTPUT_DIR)
        save_to_excel(raw, details, cats, OUTPUT_FILE)
    else:
        print(f"❌ Directory not found: {BASE_OUTPUT_DIR}")