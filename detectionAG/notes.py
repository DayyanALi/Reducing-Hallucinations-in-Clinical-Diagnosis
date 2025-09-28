import os
from dotenv import load_dotenv
import glob
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES
import json

# ---------------- CONFIG ---------------- #
load_dotenv()

input_dir = "E:/detectionAG/output/transcriptions"
output_dir = "E:/detectionAG/output/notes"
os.makedirs(output_dir, exist_ok=True)

# LLM setup
# llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

# Insert your system prompt here
system_prompt = NOTE_PROMPT
user_prompt = USER_PROMPT_NOTES

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", """Provide the SOAP consult note.

# Transcript:
# <<<
# {transcript}
# >>>

# Parameters:
# - output_format: {output_format}
# - consulting_service: {consulting_service}""")
# ])

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", user_prompt),
])

# chain = prompt | llm | JsonOutputParser()

# # ---------------- MAIN LOOP ---------------- #
# for transcript_file in glob.glob(os.path.join(input_dir, "*.txt")):
#     base = os.path.splitext(os.path.basename(transcript_file))[0]
#     output_file = os.path.join(output_dir, f"{base}.md")  # or .json

#     if os.path.exists(output_file):
#         print(f"⏩ Skipping {output_file} (already exists)")
#         continue

#     print(f"Processing {transcript_file}...")

#     # Read transcript
#     with open(transcript_file, "r", encoding="utf-8") as f:
#         transcript = f.read()

#     # Run chain
#     note = chain.invoke({
#         "transcript": transcript,
#         "output_format": "markdown",   # or "json"
#         "consulting_service": "General Medicine"
#     })

#     # Save result
#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write(note)

#     print(f"✅ Saved SOAP note → {output_file}")

# print("🎉 Done — all transcripts processed into notes.")

load_dotenv()

input_file = "E:/detectionAG/output/transcriptions/day1_consultation02.txt"
output_file = "E:/detectionAG/output/notes/sample.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# ---------------- LLM & PROMPT SETUP ---------------- #

# 1. LLM setup - Corrected the model name from "o3" to "gpt-4o"
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

# 2. Load your prompt components
system_prompt = NOTE_PROMPT 
user_prompt_template_string = USER_PROMPT_NOTES # This string MUST contain {transcript}, etc.

# 3. *** THE FIX ***
#    Define the ChatPromptTemplate correctly so it recognizes the variables.
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", user_prompt_template_string),
])

# 4. Chain setup - Use JsonOutputParser for more robust handling
chain = prompt | llm | JsonOutputParser()

# ---------------- MAIN ---------------- #
print(f"Processing {input_file}...")

try:
    # Read transcript from the input file
    with open(input_file, "r", encoding="utf-8") as f:
        transcript_content = f.read()

    # Run the chain with the required input variables
    note_json = chain.invoke({
        "transcript": transcript_content,
        "output_format": "json",
        "consulting_service": "General Medicine"
    })

    # Save the resulting JSON object
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(note_json, f, indent=2)
    
    print(f"✅ Saved SOAP note → {output_file}")

except FileNotFoundError:
    print(f"❌ ERROR: Input file not found at {input_file}")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")