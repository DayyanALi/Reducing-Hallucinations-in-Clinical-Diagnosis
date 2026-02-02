import os
import glob
import json
import sys
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Prompts
from configs.fact_extract_prompt import *
from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES

# Classes
from classes import SoapGenerator, FactExtractor

# ---------------- CONFIGURATION ---------------- #
load_dotenv()

SKIP_NOTE_GENERATION = True
CLEAN_TRANSCRIPT_DIR = "data/babylon_data_cleaned/babylonhealth primock57 main transcripts combined"
NOISY_TRANSCRIPT_DIR = "detectionAG/output/erroneous_transcripts"
BASE_OUTPUT_DIR = "detectionAG/output/rq2_stability"
CLEAN_FACTS_DIR = "detectionAG/output/extracted_facts_generated_notes/gpt-5"
NOISY_FACTS_DIR = "detectionAG/output/erroneous_note_facts"
MODELS_TO_RUN = ["gpt-5.1"]

# Safety cap to avoid token blowups
MAX_BATCH_SIZE = 10


# ---------------- ANALYST ---------------- #
class StabilityAnalyst:
    def __init__(self, model_name="gpt-5.1"):
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0
        )

    def _build_messages(self, clean_facts, noisy_facts):
        prompt_content = RQ2_DIFF_USER.format(
            clean_facts=json.dumps(clean_facts),
            noisy_facts=json.dumps(noisy_facts)
        )

        return [
            {"role": "system", "content": RQ2_DIFF_SYSTEM},
            {"role": "user", "content": prompt_content}
        ]

    def run_differential_analysis_batch(self, clean_facts, noisy_facts_list):
        """
        noisy_facts_list: List[dict]
        returns: List[dict]
        """

        messages_batch = [
            self._build_messages(clean_facts, noisy_facts)
            for noisy_facts in noisy_facts_list
        ]

        responses = self.llm.batch(messages_batch)

        outputs = []
        for response in responses:
            content = (
                response.content
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            outputs.append(json.loads(content))

        return outputs


# ---------------- HELPERS ---------------- #
def load_or_generate_facts(
    transcript_path,
    note_path,
    fact_path,
    generator,
    extractor,
    tag
):
    """
    Priority:
    1. Load facts if exist
    2. Else load note if exists → extract facts
    3. Else generate note → extract facts
    """

    if os.path.exists(fact_path):
        print(f"   [{tag}] Loading existing FACTS")
        with open(fact_path) as f:
            return json.load(f)

    if SKIP_NOTE_GENERATION and os.path.exists(note_path):
        print(f"   [{tag}] Extracting FACTS from existing NOTE")
        with open(note_path) as f:
            raw_note = json.load(f) if note_path.endswith(".json") else f.read()

        facts = extractor.to_qnote(raw_note)
        with open(fact_path, "w") as f:
            json.dump(facts, f, indent=2)
        return facts

    print(f"   [{tag}] Generating NOTE → FACTS")
    with open(transcript_path) as f:
        transcript = f.read()

    raw_note = generator.generate(transcript)
    facts = extractor.to_qnote(raw_note)

    with open(note_path, "w") as f:
        json.dump(raw_note, f, indent=2)

    with open(fact_path, "w") as f:
        json.dump(facts, f, indent=2)

    return facts


# ---------------- MAIN ---------------- #
def main():
    for model in MODELS_TO_RUN:
        for sub in ["clean_notes", "noisy_notes", "clean_facts", "noisy_facts", "reports"]:
            os.makedirs(os.path.join(BASE_OUTPUT_DIR, model, sub), exist_ok=True)

    clean_files = sorted(glob.glob(os.path.join(CLEAN_TRANSCRIPT_DIR, "*.txt")))
    print(f"Found {len(clean_files)} clean transcripts.")

    for model_name in MODELS_TO_RUN:
        print(f"\n>>> MODEL: {model_name}")

        generator = SoapGenerator(model_name)
        extractor = FactExtractor()
        analyst = StabilityAnalyst(model_name)

        for clean_path in clean_files:
            base = os.path.splitext(os.path.basename(clean_path))[0]
            print(f"\n▶ Transcript: {base}")

            noisy_paths = glob.glob(
                os.path.join(NOISY_TRANSCRIPT_DIR, f"*{base}*.txt")
            )

            if not noisy_paths:
                print("   ⚠️ No noisy variants found")
                continue

            clean_fact_path = os.path.join(CLEAN_FACTS_DIR, f"facts_{base}.json")
            if not os.path.exists(clean_fact_path):
                print(f"   ❌ Missing CLEAN facts")
                continue

            with open(clean_fact_path) as f:
                clean_facts = json.load(f)

            noisy_facts_batch = []
            metadata_batch = []

            for noisy_path in noisy_paths:
                noisy_id = os.path.splitext(os.path.basename(noisy_path))[0]
                noisy_id = noisy_id.replace("change", "error_")
                error_id = noisy_id.split("_")[-1][6:]

                report_path = os.path.join(
                    BASE_OUTPUT_DIR, model_name, "reports",
                    f"error_{error_id}_diff.json"
                )

                if os.path.exists(report_path):
                    print(f"   [SKIP] Report exists → {noisy_id}")
                    continue

                noisy_note_path = os.path.join(
                    BASE_OUTPUT_DIR, model_name, "noisy_notes", f"{noisy_id}.json"
                )
                noisy_fact_path = os.path.join(
                    NOISY_FACTS_DIR, f"facts_{noisy_id}.json"
                )

                try:
                    noisy_facts = load_or_generate_facts(
                        noisy_path,
                        noisy_note_path,
                        noisy_fact_path,
                        generator,
                        extractor,
                        "NOISY"
                    )

                    noisy_facts_batch.append(noisy_facts)
                    metadata_batch.append({
                        "noisy_id": noisy_id,
                        "error_id": error_id,
                        "report_path": report_path
                    })

                except Exception as e:
                    print(f"   ❌ Failed loading {noisy_id}: {e}")

            if not noisy_facts_batch:
                continue

            for i in range(0, len(noisy_facts_batch), MAX_BATCH_SIZE):
                batch_facts = noisy_facts_batch[i:i + MAX_BATCH_SIZE]
                batch_meta = metadata_batch[i:i + MAX_BATCH_SIZE]

                print(f"   [DIFF] Batched analysis ({len(batch_facts)} variants)")
                diffs = analyst.run_differential_analysis_batch(
                    clean_facts,
                    batch_facts
                )

                for diff, meta in zip(diffs, batch_meta):
                    with open(meta["report_path"], "w") as f:
                        json.dump({
                            "meta": {
                                "model": model_name,
                                "clean_transcript": base,
                                "noisy_transcript": meta["noisy_id"]
                            },
                            "analysis": diff
                        }, f, indent=2)

                time.sleep(0.5)  # gentle rate limiting


if __name__ == "__main__":
    main()
