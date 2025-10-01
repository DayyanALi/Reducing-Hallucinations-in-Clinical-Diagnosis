# evaluate.py

import os
import glob
import json
from typing import List, Dict
import evaluate

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ---------------------- #
# Load metrics
# ---------------------- #
rouge = evaluate.load("rouge")
bleu = evaluate.load("bleu")

# ---------------------- #
# Perplexity Model Setup
# ---------------------- #
MODEL_NAME = "gpt2"  # you can change this to another causal LM
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token


# ---------------------- #
# Evaluation Functions
# ---------------------- #
def compute_rouge(preds: List[str], refs: List[str]) -> Dict[str, float]:
    results = rouge.compute(predictions=preds, references=refs)
    return {"rouge1": results["rouge1"], "rougeL": results["rougeL"]}

def compute_bleu(preds: List[str], refs: List[str]) -> Dict[str, float]:
    results = bleu.compute(predictions=preds, references=[[r] for r in refs])
    return {"bleu": results["bleu"]}

def compute_mtr(preds: List[str], refs_highlights: List[List[str]]) -> Dict[str, float]:
    recalls = []
    for i, (pred, highlights) in enumerate(zip(preds, refs_highlights), start=1):
        matched_terms = []
        for h in highlights:
            idx = pred.lower().find(h.lower())
            if idx != -1:
                matched_terms.append((h, idx))
        if highlights:
            recalls.append(len(matched_terms) / len(highlights))
    final_score = sum(recalls) / len(recalls) if recalls else 0.0
    return {"mtr": final_score}

# ---------------------- #
# Perplexity Function
# ---------------------- #
def compute_perplexity(preds: List[str]) -> Dict[str, float]:
    inputs = tokenizer(
        preds, return_tensors="pt", padding=True, truncation=True
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    shift_logits = logits[:, :-1, :]
    shift_labels = input_ids[:, 1:]

    log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)
    target_log_probs = log_probs.gather(
        dim=-1, index=shift_labels.unsqueeze(-1)
    ).squeeze(-1)

    target_log_probs = target_log_probs * attention_mask[:, 1:].to(log_probs.dtype)
    negative_log_likelihood = -target_log_probs.sum(dim=-1) / attention_mask[:, 1:].sum(dim=-1)

    perplexities = torch.exp(negative_log_likelihood)
    mean_perplexity_score = torch.mean(perplexities)

    return {"perplexity": mean_perplexity_score.item()}

# ---------------------- #
# Load references (from single SOAP JSON file)
# ---------------------- #
def load_references_soap(json_file: str) -> Dict[str, Dict]:
    refs = {}
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        consult_name = entry["consult_name"]
        soap_text = entry["SOAP"]
        refs[consult_name] = {"note": soap_text}
    return refs

# ---------------------- #
# Main evaluation
# ---------------------- #
import os
import glob
import json
from typing import Dict, List

# ---------------------- #
# Load helpers
# ---------------------- #
def load_predictions(folder: str) -> Dict[str, str]:
    """Load generated predictions (txt/md/json)."""
    preds = {}
    for file_path in (
        glob.glob(os.path.join(folder, "*.txt"))
        + glob.glob(os.path.join(folder, "*.md"))
        + glob.glob(os.path.join(folder, "*.json"))
    ):
        with open(file_path, "r", encoding="utf-8") as f:
            fname = os.path.splitext(os.path.basename(file_path))[0]
            preds[fname] = f.read()
    return preds


def load_references(folder: str) -> Dict[str, Dict]:
    """Load reference JSONs (with highlights, notes, etc)."""
    refs = {}
    for file_path in glob.glob(os.path.join(folder, "*.json")):
        with open(file_path, "r", encoding="utf-8") as f:
            fname = os.path.splitext(os.path.basename(file_path))[0]
            refs[fname] = json.load(f)
    return refs


# ---------------------- #
# Metrics
def evaluate_folder(text_folder: str, soap_folder: str, ref_folder: str, num_files: int = None):
    """
    text_folder: generated SOAP notes
    soap_folder: gold SOAP notes (for rouge/bleu/ppl)
    ref_folder: raw references (json with highlights)
    """
    print(f"Loading predictions (generated SOAP) from: {text_folder}")
    preds = load_predictions(text_folder)
    print(f"Loaded {len(preds)} predictions")

    print(f"Loading gold SOAP notes from: {soap_folder}")
    soaps = load_references_soap(soap_folder)  # treat SOAP references as text files
    print(f"Loaded {len(soaps)} SOAP references")

    print(f"Loading raw reference JSONs from: {ref_folder}")
    refs = load_references(ref_folder)
    print(f"Loaded {len(refs)} JSON references")

    # intersection across all three
    common_files = sorted(set(preds.keys()) & set(soaps.keys()) & set(refs.keys()))
    print(f"Common files found: {len(common_files)} -> {common_files[:5]}")

    if not common_files:
        raise ValueError("No matching files across predictions, SOAP references, and raw JSON references!")

    if num_files:
        common_files = common_files[:num_files]
        print(f"Limiting evaluation to first {len(common_files)} files.")

    pred_texts, soap_texts, ref_highlights = [], [], []
    for fname in common_files:
        pred_texts.append(preds[fname])
        soap_texts.append(soaps[fname]['note'])  # gold SOAP
        ref_highlights.append(refs[fname].get("highlights", []))

    print("\nComputing metrics...")

    metrics = {}
    metrics.update(compute_rouge(pred_texts, soap_texts))
    print("ROUGE done.")

    metrics.update(compute_bleu(pred_texts, soap_texts))
    print("BLEU done.")

    metrics.update(compute_mtr(pred_texts, ref_highlights))
    print("MTR done.")

    metrics.update(compute_perplexity(pred_texts))
    print("Perplexity done.")

    print("\nFinal metrics:", metrics)
    return metrics

if __name__ == "__main__":
    pred_folder = "E:/detectionAG/output/notes_text"
    ref_json = "E:/detectionAG/output/notes_soap/Complete_Primock_SOAP_Notes.json"
    ref_highlights = "E:/detectionAG/output/reference"

    scores = evaluate_folder(pred_folder, ref_json, ref_highlights, num_files=5)

    print("Evaluation Results:")
    for k, v in scores.items():
        print(f"{k}: {v:.4f}")
