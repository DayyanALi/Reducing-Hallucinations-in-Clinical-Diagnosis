import os
import json
import glob

folder_path = "data/babylon_data/babylonhealth primock57 main notes"

# Get all JSON files in the folder
json_files = glob.glob(os.path.join(folder_path, "*.json"))

# Dictionary to store extracted substrings
extracted_data = {}

for file_path in json_files:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    note = data.get("note", "")
    if not note:
        print(f"[SKIP] No 'note' key in {os.path.basename(file_path)}")
        continue

    # Find indices for "Imp" and "DDx"
    imp_idx = note.find("Imp")
    ddx_idx = note.find("DDx")

    # Determine which comes first (and exists)
    starts = [i for i in [imp_idx, ddx_idx] if i != -1]
    start_idx = max(starts) if starts else -1
    start_idx += 5

    end_idx = note.find("Plan")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        substring = note[start_idx:end_idx].strip()
        extracted_data[os.path.basename(file_path)] = substring
    else:
        extracted_data[os.path.basename(file_path)] = None
        print(f"[WARN] Could not extract substring in {os.path.basename(file_path)}")

# Save all extracted data to a new JSON file
output_path = "detectionAG/set_4/extracted_ddx.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(extracted_data, f, indent=2, ensure_ascii=False)

print(f"\nExtraction complete. Saved to: {output_path}")
