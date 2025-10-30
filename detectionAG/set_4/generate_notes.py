import os, glob, json, time
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from detectionAG.set_4.multi_agent_system import ScribePipeline
from detectionAG.configs.notes_prompts.HP_prompt import H_AND_P_PROMPT

# ---------------- CONFIG ---------------- #
load_dotenv()

TRANSCRIPTS_DIR = "data/babylon_data/babylonhealth primock57 main transcripts combined"  # folder of *.txt transcripts
OUTPUT_ROOT = "detectionAG/output/set4new"

CONFIG_KEY = "E"   # <-- choose config (A, B, C, D)
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
    return sorted(glob.glob(os.path.join(folder, "*.txt")))

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_json(path: str, obj: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def is_completed(config: str, model: str, transcript_name: str) -> bool:
    """
    Check if output file for this config/model/transcript already exists.
    """
    output_path = os.path.join(OUTPUT_ROOT, config, model, f"{transcript_name}.json")
    return os.path.exists(output_path)

# ---------------- MAIN ---------------- #
def main():
    transcripts = load_transcripts(TRANSCRIPTS_DIR)
    print(f"Found {len(transcripts)} transcripts.")
    if not transcripts:
        print("No transcripts found. Check TRANSCRIPTS_DIR.")
        return

    for model_name in MODELS:
        print(f"\n=== Running model: {model_name} ===")

        for tpath in transcripts:
            base_name = os.path.splitext(os.path.basename(tpath))[0]
            out_path = os.path.join(OUTPUT_ROOT, CONFIG_KEY, model_name, f"{base_name}.json")

            if SKIP_EXISTING and is_completed(CONFIG_KEY, model_name, base_name):
                print(f"⏩ Skipping {base_name} ({model_name}) — already exists.")
                continue

            print(f"• Processing: {base_name} with {model_name}")
            transcript_text = read_text(tpath)

            # Run the scribe pipeline for this model/config
            try:
                scribe_pipeline = ScribePipeline(model_name=model_name,config_key=CONFIG_KEY, note_prompt=H_AND_P_PROMPT)
                note_result = scribe_pipeline.run(transcript_text)

                # Save structured JSON output
                write_json(out_path, {
                    "model": model_name,
                    "config": CONFIG_KEY,
                    "file": base_name,
                    "note": note_result,
                })

                print(f"✅ Saved: {out_path}")
            except Exception as e:
                print(f"❌ Error processing {base_name} with {model_name}: {e}")

            time.sleep(REQUEST_DELAY)

        print(f"✓ Done model: {model_name}")

if __name__ == "__main__":
    main()