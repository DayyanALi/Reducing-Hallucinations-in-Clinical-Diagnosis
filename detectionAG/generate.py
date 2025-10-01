import os
import glob
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES

# ---------------- CONFIG ---------------- #
load_dotenv()

transcript_dir = "E:/detectionAG/output/transcriptions"
output_dir_json = "E:/detectionAG/output/notes_json"
output_dir_txt = "E:/detectionAG/output/notes_text"

os.makedirs(output_dir_json, exist_ok=True)
os.makedirs(output_dir_txt, exist_ok=True)

# How many transcripts to process
num_files = 5

# Collect all txt files and take first N
all_files = sorted(glob.glob(os.path.join(transcript_dir, "*.txt")))
input_files = all_files[:num_files]

print(f"📑 Found {len(all_files)} transcripts, processing first {len(input_files)}")

# ---------------- LLM & PROMPT ---------------- #
llm = ChatOpenAI(model="gpt-5-nano", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

system_prompt = NOTE_PROMPT
user_prompt_template_string = USER_PROMPT_NOTES

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", user_prompt_template_string),
])

chain = prompt | llm | StrOutputParser()

# ---------------- MAIN ---------------- #
for idx, input_file in enumerate(input_files, start=1):
    print(f"\n📂 Processing transcript {idx}: {input_file}...")

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        inputs = {
            "transcript": transcript_content,
            "output_format": "markdown",
            "consulting_service": "General Medicine"
        }

        note_raw = chain.invoke(inputs)

        # Output file paths
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir_json, f"{base_name}.json")
        output_txt = os.path.join(output_dir_txt, f"{base_name}.txt")

        try:
            note_json = json.loads(note_raw)
            is_json = True
        except json.JSONDecodeError:
            print("⚠️ Model returned invalid JSON. Saving raw output instead.")
            note_json = note_raw
            is_json = False

        if is_json and isinstance(note_json, dict):
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(note_json, f, indent=2)
            print(f"✅ Saved structured SOAP note → {output_file}")
        else:
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(note_raw)
            print(f"✅ Saved raw text note → {output_txt}")

    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at {input_file}")
    except Exception as e:
        print(f"❌ An unexpected error occurred for {input_file}: {e}")
