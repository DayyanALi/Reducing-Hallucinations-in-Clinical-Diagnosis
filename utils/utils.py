import pandas as pd
from random import sample
import json
from typing import Any

def get_transcript(num_samples: int=1) -> str:
    df = pd.read_csv("data/challenge_data/clinicalnlp_taskB_test1.csv")
    sampled_rows = sample(list(df["dialogue"]), num_samples)
    return " ".join(sampled_rows)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
