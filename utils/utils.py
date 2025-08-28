import pandas as pd
from random import sample
import random
import json
from typing import Any
# import torch

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

def get_hidden_states(tokenizer, model, prompt: str, max_new_tokens: int = 20, device:str= "cpu"):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # with torch.no_grad():
    generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
    full_outputs = model(generated_ids, output_hidden_states=True)

    prompt_len = inputs["input_ids"].shape[1]
    full_ids = generated_ids[0]                       
    output_token_ids = full_ids[prompt_len:]          

    generated_text = tokenizer.decode(output_token_ids, skip_special_tokens=True)
    output_hidden_states = tuple(
        layer[:, prompt_len:, :].detach().cpu() for layer in full_outputs.hidden_states
    )
    return {
        "text": generated_text,
        "output_tokens": tokenizer.convert_ids_to_tokens(output_token_ids.tolist()),
        "output_hidden_states": output_hidden_states,  
    }
