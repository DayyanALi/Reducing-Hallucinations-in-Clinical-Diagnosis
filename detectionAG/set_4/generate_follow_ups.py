# from __future__ import annotations
# import os, glob, json, time
# from typing import Dict, Any

# from dotenv import load_dotenv
# import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# # Import pipeline and prompt
# from detectionAG.set_4.multi_agent_system import ScribePipeline
# from detectionAG.configs.set_4_prompts import FOLLOW_UP_QS_PROMPT

# # ---------------- CONFIG ---------------- #
# load_dotenv()

# TRANSCRIPTS_DIR = "detectionAG/set_4/transcripts_with_turns"
# DDX_JSON_PATH = "detectionAG/set_4/extracted_ddx.json" 
# OUTPUT_ROOT = "detectionAG/output/set4/follow_up_qs"

# MODELS = [
#     "o3",
#     "gpt-5-nano",
#     "gpt-4o",
#     "gpt-4.1",
#     "gpt-4.1-mini",
#     "gpt-5-mini",
#     "gpt-5",
# ]

# REQUEST_DELAY = 0.5
# RETRIES = 2
# SKIP_EXISTING = True

# # ---------------- HELPERS ---------------- #
# def load_transcripts(folder: str):
#     """Return all transcript .txt files from folder."""
#     return sorted(glob.glob(os.path.join(folder, "*.txt")))

# def read_text(path: str) -> str:
#     """Read text content from a transcript file."""
#     with open(path, "r", encoding="utf-8") as f:
#         return f.read()

# def write_json(path: str, obj: Dict[str, Any]):
#     """Save dict to JSON file."""
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(obj, f, indent=2, ensure_ascii=False)

# def is_completed(model: str, transcript_name: str) -> bool:
#     """Check if output file for this model/transcript already exists."""
#     output_path = os.path.join(OUTPUT_ROOT, model, f"{transcript_name}.json")
#     return os.path.exists(output_path)

# def load_ddx_map(path: str) -> Dict[str, str]:
#     """Load extracted_ddx.json which maps transcript filename -> ddx."""
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"DDx file not found: {path}")
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)

# # ---------------- MAIN ---------------- #
# def main():
#     transcripts = load_transcripts(TRANSCRIPTS_DIR)
#     ddx_map = load_ddx_map(DDX_JSON_PATH)

#     print(f"Found {len(transcripts)} transcripts.")
#     print(f"Loaded {len(ddx_map)} DDx entries from {DDX_JSON_PATH}\n")

#     if not transcripts:
#         print("No transcripts found. Check TRANSCRIPTS_DIR.")
#         return

#     for model_name in MODELS:
#         print(f"\n=== Running model: {model_name} ===")
#         for tpath in transcripts:
#             base_name = os.path.splitext(os.path.basename(tpath))[0]
#             out_path = os.path.join(OUTPUT_ROOT, model_name, f"{base_name}.json")

#             if SKIP_EXISTING and is_completed(model_name, base_name):
#                 print(f"⏩ Skipping {base_name} ({model_name}) — already exists.")
#                 continue

#             # Retrieve corresponding diagnosis
#             ddx = ddx_map.get(f"{base_name}.json")
#             if not ddx:
#                 print(f"⚠️ No DDx found for {base_name}, skipping.")
#                 continue

#             print(f"• Processing: {base_name} with {model_name}")
#             transcript_text = read_text(tpath)

#             try:
#                 # Initialize follow-up question pipeline
#                 scribe_pipeline = ScribePipeline(
#                     model_name=model_name,
#                     question_prompt=FOLLOW_UP_QS_PROMPT
#                 )

#                 # Call with transcript and ddx
#                 result = scribe_pipeline.run(
#                     transcript=transcript_text,
#                     ddx=ddx
#                 )
#                 print("RESULT: ", result)
#                 # Save structured output
#                 write_json(out_path, {
#                     "model": model_name,
#                     "file": base_name,
#                     "ddx_used": ddx,
#                     "questions": result.get("questions"),
#                 })

#                 print(f"✅ Saved: {out_path}")

#             except Exception as e:
#                 print(f"❌ Error processing {base_name} with {model_name}: {e}")

#             time.sleep(REQUEST_DELAY)

#         print(f"✓ Done model: {model_name}")

# if __name__ == "__main__":
#     main()

from __future__ import annotations
import os, glob, json, time, sys
from typing import Dict, Any
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import pipeline and prompt
from detectionAG.set_4.multi_agent_system import ScribePipeline
from detectionAG.configs.set_4_prompts import FOLLOW_UP_QS_PROMPT

# ---------------- CONFIG ---------------- #
load_dotenv()

# Folders and files
TRANSCRIPTS_DIR = "detectionAG/set_4/transcripts_with_turns"
DDX_JSON_PATH = "detectionAG/set_4/extracted_ddx.json"       # Used in mode 1
DDX_ROOT_DIR = "detectionAG/set_4/ddx_llm"               # Used in mode 2
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

# Behaviour
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

def read_json(path: str) -> Dict[str, Any]:
    """Read JSON file safely."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str, obj: Dict[str, Any]):
    """Save dict to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def is_completed(folder_prefix: str, model: str, transcript_name: str) -> bool:
    """
    Check if the output file already exists.
    folder_prefix: The subpath under OUTPUT_ROOT (e.g., 'ddx_note' or 'ddx_llm/ddx_source_model')
    model: Model name (e.g., 'gpt-4.1')
    transcript_name: Base transcript name
    """
    out_path = os.path.join(OUTPUT_ROOT, folder_prefix, model, f"{transcript_name}.json")
    return os.path.exists(out_path)

def load_ddx_map(path: str) -> Dict[str, str]:
    """Load extracted_ddx.json (transcript filename -> ddx text)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"DDx file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- MODES ---------------- #
def run_mode_1():
    """
    MODE 1:
    Use one combined DDx JSON (maps transcript -> ddx text).
    """
    transcripts = load_transcripts(TRANSCRIPTS_DIR)
    ddx_map = load_ddx_map(DDX_JSON_PATH)

    print(f"Found {len(transcripts)} transcripts.")
    print(f"Loaded {len(ddx_map)} DDx entries from {DDX_JSON_PATH}\n")

    for model_name in MODELS:
        print(f"\n=== Running model: {model_name} ===")

        for tpath in transcripts:
            base_name = os.path.splitext(os.path.basename(tpath))[0]
           
            out_path = os.path.join(OUTPUT_ROOT, "ddx_note", model_name, f"{base_name}.json")
            if SKIP_EXISTING and is_completed("ddx_note", model_name, base_name):
                print(f"⏩ Skipping {base_name} ({model_name}) — already exists.")
                continue

            ddx = ddx_map.get(f"{base_name}.json")
            if not ddx:
                print(f"⚠️ No DDx found for {base_name}, skipping.")
                continue

            print(f"• Processing: {base_name} [{model_name}]")
            transcript_text = read_text(tpath)

            try:
                scribe_pipeline = ScribePipeline(
                    model_name=model_name,
                    question_prompt=FOLLOW_UP_QS_PROMPT
                )

                result = scribe_pipeline.run(transcript=transcript_text, ddx=ddx)

                write_json(out_path, {
                    "model": model_name,
                    "file": base_name,
                    "ddx_source": "gold",
                    "ddx_used": ddx,
                    "questions": result.get("questions"),
                })

                print(f"✅ Saved: {out_path}")
                break

            except Exception as e:
                print(f"❌ Error processing {base_name} ({model_name}): {e}")

            time.sleep(REQUEST_DELAY)

        print(f"✓ Done model: {model_name}")


def run_mode_2():
    """
    MODE 2:
    Use multiple DDx subfolders, each containing per-transcript JSONs.
    """
    transcripts = load_transcripts(TRANSCRIPTS_DIR)
    ddx_subfolders = sorted(
        [f for f in os.listdir(DDX_ROOT_DIR) if os.path.isdir(os.path.join(DDX_ROOT_DIR, f))]
    )

    print(f"Found {len(transcripts)} transcripts.")
    print(f"Found {len(ddx_subfolders)} DDx sources under {DDX_ROOT_DIR}\n")

    for model_name in MODELS:
        print(f"\n=== Running model: {model_name} ===")

        for ddx_source_model in ddx_subfolders:
            ddx_folder = os.path.join(DDX_ROOT_DIR, ddx_source_model)
            print(f"\n-- Using DDx source: {ddx_source_model} --")
            i = 0
            for tpath in transcripts:
                i += 1
                if i == 6:
                    break
                base_name = os.path.splitext(os.path.basename(tpath))[0]
                ddx_path = os.path.join(ddx_folder, f"{base_name}.json")
                out_path = os.path.join(OUTPUT_ROOT, "ddx_llm", f"ddx_{ddx_source_model}", model_name, f"{base_name}.json")

                if SKIP_EXISTING and is_completed(f"ddx_llm/ddx_{ddx_source_model}", model_name, base_name):
                    print(f"⏩ Skipping {base_name} ({model_name}/{ddx_source_model}) — already exists.")
                    continue

                if not os.path.exists(ddx_path):
                    print(f"⚠️ No DDx file found for {base_name} in {ddx_source_model}, skipping.")
                    continue
                
                try:
                    ddx_data = read_json(ddx_path)
                    transcript_text = read_text(tpath)

                    print(f"• Processing: {base_name} [{model_name} | {ddx_source_model}]")

                    scribe_pipeline = ScribePipeline(
                        model_name=model_name,
                        question_prompt=FOLLOW_UP_QS_PROMPT
                    )

                    result = scribe_pipeline.run(
                        transcript=transcript_text,
                        ddx=ddx_data
                    )

                    write_json(out_path, {
                        "model": model_name,
                        "file": base_name,
                        "ddx_source": ddx_source_model,
                        "questions": result.get("questions"),
                    })

                    print(f"✅ Saved: {out_path}")
                    
                except Exception as e:
                    print(f"❌ Error processing {base_name} ({model_name}/{ddx_source_model}): {e}")

                time.sleep(REQUEST_DELAY)

        print(f"✓ Done model: {model_name}")

# ---------------- ENTRY ---------------- #
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Follow-up question generation for DDx experiments.")
    parser.add_argument("mode", type=int, choices=[1, 2], help="1 = single DDx JSON | 2 = subfolder DDx JSONs")
    args = parser.parse_args()

    if args.mode == 1:
        run_mode_1()
    else:
        run_mode_2()
