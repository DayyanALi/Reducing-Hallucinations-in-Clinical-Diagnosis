import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ---------------- CONFIG ---------------- #
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

INPUT_DIR = "output/reference"        # input JSONs with "note" field
OUTPUT_DIR = "output/notes_soap"      # SOAP-format notes
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- LLM ---------------- #
llm = ChatOpenAI(model="gpt-5-nano", temperature=0, api_key=api_key)

soap_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a medical scribe assistant. "
     "Convert the following unstructured medical note into a structured SOAP format "
     "(Subjective, Objective, Assessment, Plan). "),
    ("human", "{note_text}")
])

chain = soap_prompt | llm | StrOutputParser()

# ---------------- MAIN ---------------- #
def convert_notes_to_soap(input_dir, output_dir, limit=None):
    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".json")])
    if limit:
        files = files[:limit]

    for fname in files:
        input_path = os.path.join(input_dir, fname)
        output_path = os.path.join(output_dir, fname.replace(".json", "_soap.json"))

        print(f"📂 Converting {fname} → SOAP")

        # Load JSON and extract "note"
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_note = data.get("note", "").strip()
        if not raw_note:
            print(f"⚠️ Skipping {fname} (no 'note' field found).")
            continue

        # Call GPT chain
        soap_raw = chain.invoke({"note_text": raw_note})

        try:
            soap_json = json.loads(soap_raw)
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON for {fname}, saving raw output instead.")
            soap_json = {"raw_output": soap_raw}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(soap_json, f, indent=2)

        print(f"✅ Saved SOAP note → {output_path}")


if __name__ == "__main__":
    # set limit=N if you only want first N files
    convert_notes_to_soap(INPUT_DIR, OUTPUT_DIR, limit=5)
