import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES

# ---------------- CONFIG ---------------- #
load_dotenv()

input_file = "E:/detectionAG/output/transcriptions/day1_consultation02.txt"
output_file = "E:/detectionAG/output/notes/sample.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

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
print(f"📂 Reading transcript from {input_file}...")

try:
    with open(input_file, "r", encoding="utf-8") as f:
        transcript_content = f.read()

    # Debug: show a preview of the transcript
    print("\n--- TRANSCRIPT PREVIEW ---")
    print(transcript_content[:500])  # first 500 chars
    print("--- END TRANSCRIPT PREVIEW ---\n")

    # Debug: show what’s being passed into the chain
    inputs = {
        "transcript": transcript_content,
        "output_format": "json",
        "consulting_service": "General Medicine"
    }
    print("🔍 Inputs to chain:", inputs.keys())
    print("Transcript length:", len(inputs["transcript"]))

    # Run chain
    note_raw = chain.invoke(inputs)

    # Debug: show raw LLM output
    print("\n--- RAW LLM OUTPUT ---")
    print(note_raw[:1000])  # preview
    print("--- END RAW LLM OUTPUT ---\n")

    # Try parsing JSON
    try:
        note_json = json.loads(note_raw)
    except json.JSONDecodeError:
        print("⚠️ Model returned invalid JSON. Saving raw output instead.")
        note_json = note_raw

    # Save result
    with open(output_file, "w", encoding="utf-8") as f:
        if isinstance(note_json, dict):
            json.dump(note_json, f, indent=2)
        else:
            f.write(note_json)

    print(f"✅ Saved SOAP note → {output_file}")

except FileNotFoundError:
    print(f"❌ ERROR: Input file not found at {input_file}")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
