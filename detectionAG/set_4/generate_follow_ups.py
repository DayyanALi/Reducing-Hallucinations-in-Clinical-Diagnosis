from __future__ import annotations
import os, glob, json, time
from typing import Dict, Any

from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import pipeline and prompt
from detectionAG.set_4.multi_agent_system import ScribePipeline
from detectionAG.configs.set_4_prompts import FOLLOW_UP_QS_PROMPT

# ---------------- CONFIG ---------------- #
load_dotenv()

TRANSCRIPTS_DIR = "detectionAG/set_4/transcripts_with_turns"
DDX_JSON_PATH = "detectionAG/set_4/extracted_ddx.json" 
OUTPUT_ROOT = "detectionAG/output/set4/follow_up_qs"

MODELS = [
    "o3",
    "gpt-5-nano",
    "gpt-4o",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-5-mini",
    "gpt-5",
]

REQUEST_DELAY = 0.5
RETRIES = 2
SKIP_EXISTING = True

# ---------------- HELPERS ---------------- #
def load_transcripts(folder: str):
    """Return all transcript .txt files from folder."""
    return sorted(glob.glob(os.path.join(folder, "*.txt")))

def read_text(path: str) -> str:
    """Read text content from a transcript file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_json(path: str, obj: Dict[str, Any]):
    """Save dict to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def is_completed(model: str, transcript_name: str) -> bool:
    """Check if output file for this model/transcript already exists."""
    output_path = os.path.join(OUTPUT_ROOT, model, f"{transcript_name}.json")
    return os.path.exists(output_path)

def load_ddx_map(path: str) -> Dict[str, str]:
    """Load extracted_ddx.json which maps transcript filename -> ddx."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"DDx file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- MAIN ---------------- #
def main():
    transcripts = load_transcripts(TRANSCRIPTS_DIR)
    ddx_map = load_ddx_map(DDX_JSON_PATH)

    print(f"Found {len(transcripts)} transcripts.")
    print(f"Loaded {len(ddx_map)} DDx entries from {DDX_JSON_PATH}\n")

    if not transcripts:
        print("No transcripts found. Check TRANSCRIPTS_DIR.")
        return

    for model_name in MODELS:
        i = 0
        print(f"\n=== Running model: {model_name} ===")
        for tpath in transcripts:
            i += 1
            if i == 7:
                break
            base_name = os.path.splitext(os.path.basename(tpath))[0]
            out_path = os.path.join(OUTPUT_ROOT, model_name, f"{base_name}.json")

            if SKIP_EXISTING and is_completed(model_name, base_name):
                print(f"⏩ Skipping {base_name} ({model_name}) — already exists.")
                continue

            # Retrieve corresponding diagnosis
            ddx = ddx_map.get(f"{base_name}.json")
            if not ddx:
                print(f"⚠️ No DDx found for {base_name}, skipping.")
                continue

            print(f"• Processing: {base_name} with {model_name}")
            transcript_text = read_text(tpath)

            try:
                # Initialize follow-up question pipeline
                scribe_pipeline = ScribePipeline(
                    model_name=model_name,
                    question_prompt=FOLLOW_UP_QS_PROMPT
                )

                # Call with transcript and ddx
                result = scribe_pipeline.run(
                    transcript=transcript_text,
                    ddx=ddx
                )
                print("RESULT: ", result)
                # Save structured output
                write_json(out_path, {
                    "model": model_name,
                    "file": base_name,
                    "ddx_used": ddx,
                    "questions": result.get("questions"),
                })

                print(f"✅ Saved: {out_path}")

            except Exception as e:
                print(f"❌ Error processing {base_name} with {model_name}: {e}")

            time.sleep(REQUEST_DELAY)

        print(f"✓ Done model: {model_name}")

if __name__ == "__main__":
    main()
