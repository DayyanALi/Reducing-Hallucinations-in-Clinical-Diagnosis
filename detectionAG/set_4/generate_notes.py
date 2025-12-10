from __future__ import annotations
import os, glob, json, time
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from detectionAG.set_4.multi_agent_system import ScribePipeline
from detectionAG.configs.notes_prompts_with_ddx.HP_prompt import H_AND_P_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.HP_detailed_prompt import H_AND_P_DETAILED_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.HP_super_detailed_prompt import H_AND_P_SUPER_DETAILED_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.concise_note_prompt import CONCISE_NOTE_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.soap_prompt import SOAP_NOTE_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.soap_action_plan_prompt import SOAP_ACTION_PLAN_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.problem_list_prompt import PROBLEM_LIST_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.ENT_specialist_prompt import ENT_SPECIALIST_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.indigenous_health_assessment_0_14_prompt import INDIGENOUS_HEALTH_ASSESSMENT_0_14_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.indigenous_health_assessment_15_54_prompt import INDIGENOUS_HEALTH_ASSESSMENT_15_54_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.indigenous_health_assessment_55_plus_prompt import INDIGENOUS_HEALTH_ASSESSMENT_55_PLUS_WITH_DDX_PROMPT
from detectionAG.configs.notes_prompts_with_ddx.mental_health_care_prompt import MENTAL_HEALTH_CARE_PLAN_WITH_DDX_PROMPT

# ---------------- CONFIG ---------------- #
load_dotenv()
TRANSCRIPTS_DIR = "data/babylon_data/babylonhealth primock57 main transcripts combined"
DDX_ROOT = "detectionAG/output/set4/E"
OUTPUT_ROOT = "detectionAG/output/set4"
CONFIG_KEY = "B"

NOTE_TYPES = {
    "H_AND_P": H_AND_P_WITH_DDX_PROMPT,
    "H_AND_P_DETAILED": H_AND_P_DETAILED_WITH_DDX_PROMPT,
    "H_AND_P_SUPER_DETAILED": H_AND_P_SUPER_DETAILED_WITH_DDX_PROMPT,
    "CONCISE_NOTE": CONCISE_NOTE_WITH_DDX_PROMPT,
    "PROBLEM_LIST": PROBLEM_LIST_WITH_DDX_PROMPT,
    "SOAP": SOAP_NOTE_WITH_DDX_PROMPT,
    "SOAP_ACTION_PLAN": SOAP_ACTION_PLAN_WITH_DDX_PROMPT,
    "ENT_SPECIALIST": ENT_SPECIALIST_WITH_DDX_PROMPT,
    "Indigenous Health Assessment (0-14yrs)": INDIGENOUS_HEALTH_ASSESSMENT_0_14_WITH_DDX_PROMPT,
    "Indigenous Health Assessment (15-54yrs)": INDIGENOUS_HEALTH_ASSESSMENT_15_54_WITH_DDX_PROMPT,
    "Indigenous Health Assessment (55 plus)": INDIGENOUS_HEALTH_ASSESSMENT_55_PLUS_WITH_DDX_PROMPT,
    "Mental Health Care": MENTAL_HEALTH_CARE_PLAN_WITH_DDX_PROMPT,
}

MODELS = [
    "o3", "gpt-5-nano", "gpt-4o", "gpt-4.1",
    "gpt-4.1-mini", "gpt-5-mini", "gpt-5",
]

MAX_WORKERS = 6
REQUEST_DELAY = 0.5
SKIP_EXISTING = True

# ---------------- HELPERS ---------------- #
def load_transcripts(folder: str):
    return sorted(glob.glob(os.path.join(folder, "*.txt")))

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str, obj: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def is_completed(config: str, note_type: str, model: str, transcript_name: str) -> bool:
    output_path = os.path.join(OUTPUT_ROOT, config, note_type, model, f"{transcript_name}.json")
    return os.path.exists(output_path)

def get_ddx_for_transcript(model_name: str, transcript_name: str) -> str | None:
    """
    Locate and return the DDX JSON (as a string) corresponding to a transcript and model.
    """
    ddx_path = os.path.join(DDX_ROOT, model_name, f"{transcript_name}.json")
    if not os.path.exists(ddx_path):
        return None
    try:
        ddx_json = read_json(ddx_path)
        ddx_content = ddx_json.get("note", {}).get("ddx", {})
        return json.dumps(ddx_content, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to load DDX for {transcript_name} ({model_name}): {e}")
        return None

# ---------------- TASK FUNCTION ---------------- #
def process_transcript(note_type: str, model_name: str, tpath: str, note_prompt):
    base_name = os.path.splitext(os.path.basename(tpath))[0]
    out_path = os.path.join(OUTPUT_ROOT, CONFIG_KEY, note_type, model_name, f"{base_name}.json")

    if SKIP_EXISTING and is_completed(CONFIG_KEY, note_type, model_name, base_name):
        return f"⏩ Skipped {base_name} ({model_name}, {note_type})"

    try:
        transcript_text = read_text(tpath)
        ddx_text = get_ddx_for_transcript(model_name, base_name)
        
        if not ddx_text:
            ddx_text = "No DDX data found for this model/transcript."

        scribe_pipeline = ScribePipeline(model_name=model_name, config_key=CONFIG_KEY, note_prompt=note_prompt)
        note_result = scribe_pipeline.run(transcript=transcript_text, ddx=ddx_text)

        write_json(out_path, {
            "model": model_name,
            "config": CONFIG_KEY,
            "note_type": note_type,
            "file": base_name,
            "note": note_result,
        })
        time.sleep(REQUEST_DELAY)
        return f"✅ Saved {base_name} ({model_name}, {note_type})"

    except Exception as e:
        return f"❌ Error {base_name} ({model_name}, {note_type}): {e}"

# ---------------- MAIN ---------------- #
def main():
    transcripts = load_transcripts(TRANSCRIPTS_DIR)
    print(f"Found {len(transcripts)} transcripts.")
    if not transcripts:
        print("No transcripts found. Check TRANSCRIPTS_DIR.")
        return

    tasks = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for note_type, note_prompt in NOTE_TYPES.items():
            for model_name in MODELS:
                for tpath in transcripts:
                    tasks.append(executor.submit(process_transcript, note_type, model_name, tpath, note_prompt))
                    

        for future in as_completed(tasks):
            print(future.result())
    print("\n🎯 All threaded note generations completed.")

if __name__ == "__main__":
    main()