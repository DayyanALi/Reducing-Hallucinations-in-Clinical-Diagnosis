import pandas as pd
from random import sample
import random
import json
from typing import Any, List
from utils.data_types import Transcript_Notes_record


def get_transcript_with_diagnoses(num_samples: int=1) -> str:
    df = pd.read_csv("data/challenge_data/clinicalnlp_taskB_test1.csv")
    sampled_rows = sample(list(df["dialogue"]), num_samples)
    return " ".join(sampled_rows)
    

def _extract_records_container(data: Any) -> List[dict[str, Any]]:
    if isinstance(data, list):
        if all(isinstance(x, dict) for x in data):
            return data

    if isinstance(data, dict):
        # Common container keys
        for key in ("data", "train", "records", "items", "examples", "samples"):
            v = data.get(key)
            if isinstance(v, list) and all(isinstance(x, dict) for x in v):
                return v

        # Dict of id -> record
        if all(isinstance(v, dict) for v in data.values()):
            return list(data.values())

    raise TypeError(
        "Unsupported JSON structure. Expected a list of dicts, a dict containing such a list, "
        "or a dict of id->record."
    )

def get_transcript_with_notes(num_samples: int = 1, *, seed: int | None = None) -> List[Transcript_Notes_record]:
    if seed is not None:
        random.seed(seed)

    with open("data/challenge_data/train.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    population = _extract_records_container(raw)

    if num_samples > len(population):
        raise ValueError(f"Requested {num_samples} samples, but only {len(population)} available.")

    sampled = random.sample(population, num_samples)

    records: List[Transcript_Notes_record] = []
    for i, item in enumerate(sampled):
        # Be forgiving about key names and missing ids
        transcript = item.get("src", "")
        notes = item.get("tgt", item.get("tgt", ""))
        rid = item.get("file")
        records.append(Transcript_Notes_record(transcript=transcript, notes=notes, file=str(rid)))

    return records

def get_transcript_with_no_hall(num_samples: int=1) -> str:
    with open("data/challenge_data/train_with_diagnoses.json", "r") as f:
        data = json.load(f)

    # Randomly select num_samples entries
    if num_samples > len(data):
        raise ValueError(f"Requested {num_samples} samples, but only {len(data)} available.")

    sampled_data = random.sample(data, num_samples)

    return sampled_data

def get_transcript_with_context_hall(num_samples: int=1) -> str:
    with open("data/challenge_data/Contextual_hallucination_data.json", "r") as f:
        data = json.load(f)

    # Randomly select num_samples entries
    if num_samples > len(data):
        raise ValueError(f"Requested {num_samples} samples, but only {len(data)} available.")

    sampled_data = random.sample(data, num_samples)

    return sampled_data
    
def get_transcript_with_consistent_hall(num_samples: int=1) -> str:
    with open("data/challenge_data/Consistency_hallucinated_data.json", "r") as f:
        data = json.load(f)

    # Randomly select num_samples entries
    if num_samples > len(data):
        raise ValueError(f"Requested {num_samples} samples, but only {len(data)} available.")

    sampled_data = random.sample(data, num_samples)

    return sampled_data

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
