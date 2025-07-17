import json
from utils.utils import load_json
from typing import Any, Dict, List, Optional
from hallucination.hallucination_generation.hallucination_types import ContextualHallucinationInjector
from generator.clients import get_openai_gpt4

def inject_hallucination(
    path: str = "data/challenge_data/train_with_diagnoses.json",
    model: Any = None,
    output_path: str = "data/challenge_data/train_with_contextual_hallucination.json",
    hallucination_type: str = "contextual"
):
    records: List[Dict] = load_json(path)
    augmented: List[Dict] = []
    
    if hallucination_type == "contextual":
        injector = ContextualHallucinationInjector(model)

    print(f"Adding {hallucination_type} hallucination...")
    for rec in records:
        new_rec = injector.inject(rec)
        if new_rec:
            augmented.append(new_rec)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(augmented, f, indent=2)

    print(f"✅ Wrote {len(augmented)} augmented records to {output_path}")

if __name__ == "__main__":
    model = get_openai_gpt4()
    inject_hallucination(model=model)