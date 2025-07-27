import pandas as pd
from random import sample
import random
import json
from typing import Any

def get_transcript(num_samples: int=1) -> str:
    df = pd.read_csv("data/challenge_data/clinicalnlp_taskB_test1.csv")
    sampled_rows = sample(list(df["dialogue"]), num_samples)
    return " ".join(sampled_rows)

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
