import json
from random import choice
from typing import Any, Dict, List
from generator.clients import get_openai_gpt4
from generator.output_parsers import get_StrOutputParser
from generator.prompt_template import get_inject_contextual_hallucination_prompt
from utils.utils import load_json

def inject_contextual_hallucination(
    path: str = "data/challenge_data/train_with_diagnoses.json",
    model: Any = None,
    output_path: str = "data/challenge_data/train_with_contextual_hallucination.json"
):
    records: List[Dict] = load_json(path)
    augmented: List[Dict] = []
    
    prompt = get_inject_contextual_hallucination_prompt()
    parser = get_StrOutputParser()

    hallucination_chain = prompt | model | parser

    for rec in records:
        diagnoses = rec.get("diagnoses", [])
        if not diagnoses:
            continue
        transcript = rec.get("src") or rec.get("dialogue") or ""
        random_diagnosis = choice(diagnoses)
        original_diagnosis = random_diagnosis["diagnosis"]
        original_rationale  = random_diagnosis["rationale"]

        transcript = rec.get("src") or rec.get("transcript") or ""
        hallucinated_rationale = hallucination_chain.invoke({"transcript": transcript,"diagnosis": original_diagnosis,"rationale": original_rationale})

        new_rec = dict(rec)  
        new_rec["original_diagnosis"]    = original_diagnosis
        new_rec["original_rationale"]    = original_rationale
        new_rec["hallucinated_rationale"] = hallucinated_rationale
        new_rec["error_type"]            = "contextual_hallucination"

        augmented.append(new_rec)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(augmented, f, indent=2)

    print(f"✅ Wrote {len(augmented)} augmented records to {output_path}")

model = get_openai_gpt4()
inject_contextual_hallucination(model=model)