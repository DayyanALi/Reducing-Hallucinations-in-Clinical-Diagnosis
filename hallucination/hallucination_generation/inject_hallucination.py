import json
from utils.utils import load_json, get_transcript_with_notes
from utils.data_types import to_serializable
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
from hallucination.hallucination_generation.hallucination_types import (
    ContextualHallucinationInjector,
    ConsistencyHallucinationInjector,
    HallucinationInjector
)
from generator.clients import openai_gpt5nano

def inject_hallucination(
    model: Any = None,
    output_path: str = "data/challenge_data/train_with_contextual_hallucination.json",
    hallucination_type: str = "contextual"
):
    records: List[Any] = get_transcript_with_notes(67)
    augmented: List[Any] = []

    injector = HallucinationInjector(model=model,hallucination_type=hallucination_type)

    print(f"Adding {hallucination_type} hallucination...")

    for rec in records:
        new_rec = injector.inject_in_notes(rec)
        if new_rec:
            augmented.append(new_rec)
            print("new_rec",new_rec)
        break

    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(augmented, f, default=to_serializable, ensure_ascii=False, indent=2)
    # with open(output_path, "w", encoding="utf-8") as f:
    #     json.dump(augmented, f, indent=2)

    print(f"✅ Wrote {len(augmented)} augmented records to {output_path}")

if __name__ == "__main__":
    load_dotenv()
    model = openai_gpt5nano()

    inject_hallucination(
        model=model,
        hallucination_type="contextual",  # or "consistency"
        output_path="data/challenge_data/check_path.json"
    )
