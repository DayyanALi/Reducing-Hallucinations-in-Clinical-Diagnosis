import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES

# ---------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------
load_dotenv()

csv_path = "detectionAG/RQ2/final_all_consults_errors.csv"  
transcripts_root = "data/babylon_data_cleaned/babylonhealth primock57 main transcripts combined"
output_altered_dir = "detectionAG/output/erroneous_transcripts_4o"
output_json_dir = "detectionAG/output/erroneous_notes_4o"
output_txt_dir = "detectionAG/output/erroneous_notes_4o"

os.makedirs(output_altered_dir, exist_ok=True)
os.makedirs(output_json_dir, exist_ok=True)
os.makedirs(output_txt_dir, exist_ok=True)

# ---------------------------------------------------------------------
# LOAD CORRECTION INSTRUCTIONS
# ---------------------------------------------------------------------
df = pd.read_csv(csv_path)

required_cols = [
    "consult_name", "original_source_text", "altered_source_text"
]

if not all(col in df.columns for col in required_cols):
    raise ValueError(f"CSV missing required columns. Need: {required_cols}")

# Group by consult name to avoid repeated file reads
correction_groups = df.groupby("consult_name")
def normalize_name(raw_name: str) -> str:

    """
    Convert something like:
        facts_day4_consultation08
    to:
        day4_consultation08
    """

    # remove prefix "facts_" only if present
    if raw_name.startswith("facts_"):
        raw_name = raw_name[len("facts_"):]
    
    return raw_name

# ---------------------------------------------------------------------
# LLM Setup
# ---------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

prompt = ChatPromptTemplate.from_messages([
    ("system", NOTE_PROMPT),
    ("human", USER_PROMPT_NOTES),
])

chain = prompt | llm | StrOutputParser()
count = 0
# ---------------------------------------------------------------------
# PROCESS EACH CONSULT, ONE CHANGE AT A TIME
# ---------------------------------------------------------------------
for consult_name, group in correction_groups:

    consult_name = normalize_name(consult_name)
    transcript_path = os.path.join(transcripts_root, f"{consult_name}.txt")

    if not os.path.exists(transcript_path):
        print(f"❌ Missing transcript: {consult_name}")
        continue

    # Read file
    with open(transcript_path, "r", encoding="utf-8") as f:
        original_transcript = f.read()

    # Loop through each correction **individually**
    for idx, row in group.iterrows():
        original = str(row["original_source_text"]).strip()
        altered = "" if pd.isna(row["altered_source_text"]) else str(row["altered_source_text"]).strip()
        err_id = row["error_id"]
        transcript = original_transcript  # start from original each time
        changed = False
        print(f"--- Processing {consult_name}, error {err_id} ---")

        # Apply single replacement
        if original in transcript:
            transcript = transcript.replace(original, altered)
            changed = True
            count += 1
            print(f"changed {count}/6")
        else:
            print(f"⚠️ Skip: '{original}' not found in {consult_name}")
            continue  # skip to next correction

        if original in transcript:
            print(f"↪️ No edits made for this change in: {consult_name}")
            continue

        # Save altered transcript for this single change
        altered_file_name = f"{consult_name}_change{idx}.txt"
        altered_path = os.path.join(output_altered_dir, altered_file_name)

        with open(altered_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        print(f"✅ Saved altered transcript → {altered_path}")
        print("Applied change:", altered)
        print("Original text:", original)

        # -----------------------------------------------------------------
        # Generate SOAP note for this single change
        # -----------------------------------------------------------------
        # Save output
        json_target = os.path.join(output_json_dir, f"{consult_name}_error_{err_id}.json")
        text_target = os.path.join(output_txt_dir, f"{consult_name}_error_{err_id}.txt")
        
        # Skip if either file already exists
        if os.path.exists(json_target) or os.path.exists(text_target):
            print(f"⏭️ Note already exists for {consult_name} error {err_id}, skipping...")
            continue

        inputs = {
            "transcript": transcript,
            "output_format": "markdown",
            "consulting_service": "General Medicine",
        }

        note_raw = chain.invoke(inputs)

        try:
            parsed = json.loads(note_raw)
            if isinstance(parsed, dict):
                with open(json_target, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, indent=2)
                print(f"🟢 Saved JSON note → {json_target}")
            else:
                raise ValueError()
        except Exception:
            with open(text_target, "w", encoding="utf-8") as f:
                f.write(note_raw)
            print(f"🟡 Saved raw note text → {text_target}")
    if count == 50:
        break


print(f"{count}/{len(df)} processed.")