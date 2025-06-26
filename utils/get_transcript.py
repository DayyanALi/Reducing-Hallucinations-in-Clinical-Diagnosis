import pandas as pd
from random import sample

def get_transcript(num_samples: int=1) -> str:
    df = pd.read_csv("data/challenge_data/clinicalnlp_taskB_test1.csv")
    sampled_rows = sample(list(df["dialogue"]), num_samples)
    return " ".join(sampled_rows)


# print(get_transcript())