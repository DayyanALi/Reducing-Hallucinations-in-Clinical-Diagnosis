import os
import csv
import json
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

# --- CONFIG ---
ERROR_CSV = Path("detectionAG/final_all_consults_errors.csv")
ERROR_NOTES_DIR = Path("detectionAG/output/erroneous_notes_text")
OUTPUT_CSV = Path("detectionAG/errors_with_status.csv")
VERIFIER_MODEL = "gpt-5.1"

# Updated Prompt template for evaluating error handling
SYSTEM_PROMPT = """
You are an assistant that evaluates how an injected error in a clinical transcript was handled in an LLM-generated clinical note.
You are given the original text and the corrupted text from the transcript and the generated clinical note.
Return the status, one of:
- omitted: fact omitted from the note entirely
- preserved: error preserved in the note
- flagged as unreasonable: erroneous fact was flagged as unreasonable or ambiguous in the note
- hallucinated and corrected: the note contained the information in the original text as a result of LLM inference
- hallucinated and incorrect: the note contained incorrect information about the fact not present in either the original or altered text
Also return the exact excerpt from the note that supports your determination.
Do not include any other commentary or explanation.
"""

USER_PROMPT = """
Original source text: {original_text}
Altered source text: {altered_text}
Note: {note_text}
What is the treatment status of the error?
Return only JSON with two keys:
{{
  "status": "<one of: omitted, preserved, flagged as unreasonable, hallucinated and corrected, hallucinated and incorrect>",
  "excerpt": "<the exact excerpt from the note that supports this status>"
}}
"""

class ErrorEvaluator:
    def __init__(self, model: str = VERIFIER_MODEL):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            max_retries=3
        )

    def evaluate_error(self, note_text: str, original_text: str, altered_text: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", USER_PROMPT),
        ])
        chain = prompt | self.llm
        result_obj = chain.invoke({
            "note_text": note_text,
            "original_text": original_text,
            "altered_text": altered_text
        })
        
        # Convert AIMessage to string if necessary
        result_text = result_obj.content if hasattr(result_obj, "content") else str(result_obj)
        
        try:
            result = json.loads(result_text)
            status = result.get("status", "unknown")
            excerpt = result.get("excerpt", "")
            print(f"Evaluation Result: status={status}, excerpt={excerpt}")
            return status, excerpt

        except Exception:
            # fallback: return the raw text if JSON parsing fails
            return result_text.strip()


def main():
    evaluator = ErrorEvaluator()

    # Read CSV
    rows = []
    with open(ERROR_CSV, newline='', encoding='utf-8') as f:
        print(f"Reading errors from {ERROR_CSV}"    )
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ['status'] + ['excerpt']
        for row in reader:
            rows.append(row)

    # Process each row
    processed_rows = []
    for row in tqdm(rows):
        error_id = row['error_id']
        consult_name = row['consult_name']
        filename = f"{consult_name[6:]}_error_{error_id}.txt"
        note_path = ERROR_NOTES_DIR / filename

        if not note_path.exists():
            print(f"⚠️  Note file not found: {note_path}")
            continue  # skip row if note does not exist

        with open(note_path, 'r', encoding='utf-8') as f:
            print(f" Found note text from {note_path}")
            note_text = f.read()

        original_text = row.get('original_source_text', '')
        altered_text = row.get('altered_source_text', '')

        try:
            status, excerpt = evaluator.evaluate_error(note_text, original_text, altered_text)
        except Exception as e:
            status = f"Error: {str(e)}"

        row['status'] = status
        row['excerpt'] = excerpt
        processed_rows.append(row)

    # Write new CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)

    print(f"Saved evaluated CSV to {OUTPUT_CSV}")


if __name__ == '__main__':
    main()