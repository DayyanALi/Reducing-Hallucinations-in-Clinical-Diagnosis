# detectionAG/run_batch_eval.py
from __future__ import annotations
import os, glob, json, time
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from detectionAG.promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES
from detectionAG.detection_agent import DetectionAgent  # ensure class name matches

# ---------------- CONFIG ---------------- #
load_dotenv()

TRANSCRIPTS_DIR = "data/babylon_data/generated_joined_transcripts"   # folder of *.txt transcripts
OUTPUT_ROOT = "detectionAG/output/evaluations_set2"
NOTES_SUBDIR_TEXT = "notes_markdown"
EVALS_SUBDIR = "evals"
OUTPUT_FORMAT = "markdown"

DETECTION_MODEL = "gpt-5"
MODELS = [
    "o3",
    "gpt-5-nano",
    "gpt-4o",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-5-mini",
    "gpt-5",
]

REQUEST_DELAY = 0.5      # seconds between API calls
RETRIES = 2              # simple retry on transient failures
SKIP_EXISTING = True     # skip if note + eval already exist

# ---------------- Prompt pipeline (text out) ---------------- #
PROMPT = ChatPromptTemplate.from_messages([
    ("system", NOTE_PROMPT),
    ("human", USER_PROMPT_NOTES),
])

def ensure_dirs_for_model(model_name: str) -> Dict[str, str]:
    base = os.path.join(OUTPUT_ROOT, model_name)
    paths = {
        "notes_text": os.path.join(base, NOTES_SUBDIR_TEXT),
        "evals": os.path.join(base, EVALS_SUBDIR),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths

def load_transcripts(folder: str):
    return sorted(glob.glob(os.path.join(folder, "*.txt")))

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, data: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)

def write_json(path: str, obj: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def maybe_skip(note_txt_path: str, eval_json_path: str) -> bool:
    return SKIP_EXISTING and os.path.exists(note_txt_path) and os.path.exists(eval_json_path)

def generate_note_text(llm: ChatOpenAI, transcript_text: str, consulting_service: str = "General Medicine") -> str:
    """
    Always returns TEXT (markdown/plain). No JSON parsing or saving.
    """
    inputs = {
        "transcript": transcript_text,
        "output_format": OUTPUT_FORMAT,    # still routed to the prompt, but we treat output as text
        "consulting_service": consulting_service,
    }
    chain = PROMPT | llm | StrOutputParser()
    for attempt in range(RETRIES + 1):
        try:
            return chain.invoke(inputs)
        except Exception:
            if attempt >= RETRIES:
                raise
            # time.sleep(1.0 + 0.5 * attempt)

def run_eval_for_pair(agent: DetectionAgent, transcript_text: str, generated_note_text: str) -> Dict[str, Any]:
    return agent.run_all(baseline_text=transcript_text, candidate_text=generated_note_text)

def main():
    transcripts = load_transcripts(TRANSCRIPTS_DIR)
    print(f"Found {len(transcripts)} transcripts.")
    if not transcripts:
        print("No transcripts found. Check TRANSCRIPTS_DIR.")
        return

    for model_name in MODELS:
        print(f"\n=== Running model: {model_name} ===")
        paths = ensure_dirs_for_model(model_name)

        llm = ChatOpenAI(model=model_name)          # do not force temperature for models that don't support it
        detector = DetectionAgent(model=DETECTION_MODEL) # same here

        for tpath in transcripts:
            base_name = os.path.splitext(os.path.basename(tpath))[0]
            note_txt_path = os.path.join(paths["notes_text"], f"{base_name}.txt")
            eval_json_path = os.path.join(paths["evals"], f"{base_name}.json")

            if maybe_skip(note_txt_path, eval_json_path):
                print(f"• Skipping (exists): {base_name}")
                continue

            print(f"• Processing: {base_name}")
            transcript_text = read_text(tpath)

            # 1) Generate note (TEXT ONLY)
            t0 = time.time()
            note_text = generate_note_text(llm, transcript_text)
            gen_secs = time.time() - t0

            # Save note as text only
            write_text(note_txt_path, note_text)

            # 2) Deception analysis
            t1 = time.time()
            eval_result = run_eval_for_pair(detector, transcript_text, note_text)
            eval_secs = time.time() - t1

            # 3) Persist eval with metadata (JSON)
            payload = {
                "model": model_name,
                "file": base_name,
                "generation_seconds": round(gen_secs, 3),
                "evaluation_seconds": round(eval_secs, 3),
                "results": eval_result,
            }
            write_json(eval_json_path, payload)

            # time.sleep(REQUEST_DELAY)

        print(f"✓ Done model: {model_name}")

if __name__ == "__main__":
    main()
