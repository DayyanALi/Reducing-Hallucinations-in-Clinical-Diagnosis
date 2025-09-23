from utils import get_model, chat_change_with_answer, find_first_and_next_token_for_chat
import os
import json
import spacy
import torch

nlp = spacy.load("en_ner_bc5cdr_md")
os.environ["CUDA_VISIBLE_DEVICES"] = "7"
model_type = "7b"
model_family = "llamabase"

wiki_path = "./auto-labeled/wiki"
output_path = f"./auto-labeled/output/{model_family}{model_type}"
model, tokenizer, generation_config, at_id = get_model(model_type, model_family, 1)

topk_first_token = 4
topk_next_token = topk_first_token
windows = 16
if "llama" in model_family or "baichuan" in model_family:
    st = "▁"
else:
    st = "Ġ"

# Define medical entity types to focus on
MEDICAL_ENTITY_TYPES = {
    'DISEASE', 'SYMPTOM', 'ANATOMY', 'CHEMICAL', 'PHARMACEUTICAL', 
    'PROCEDURE', 'DEVICE', 'CONDITION'
}

prompt_chat = []

def delete_substrings(lst):
    substrings = []
    lst = list(set(lst))
    for s in lst:
        if any(s in o for o in lst if o != s):
            substrings.append(s)
    for s in substrings:
        lst.remove(s)
    return lst

def find_boundaries(text, words):
    boundaries = []
    for word in words:
        start = 0
        ntext = text
        while True:
            start = ntext.find(word)
            if start == -1:
                break
            end = start + len(word) - 1
            while start > 0 and ntext[start-1] != " ":
                start -= 1
            while end < len(ntext)-1 and ntext[end+1] != " ":
                end += 1
            boundaries.append("".join([ntext[i] for i in range(start, end+1)]))
            ntext = ntext[end+1:]
    return boundaries


def get_entities(note):
    doc = nlp(note)
    entities = [ent.text for ent in doc.ents if ent.label_ in MEDICAL_ENTITY_TYPES]
    entities = list(set(entities))
    entities = find_boundaries(note,entities)
    entities = delete_substrings(entities)

    all_entities = []
    for i in range(len(note)):
        for e in entities:
            if note[i:].startswith(e):
                all_entities.append((e, i))
                
    return all_entities

def find_first_and_next_token_for_chat(text, e, idx, input_id):
    new_text = f"{text[:idx].strip()} {text[idx:].replace(e, e + ' @', 1).strip()}" 
    new_input_id = chat_change_with_answer(prompt_chat, new_text.strip(), tokenizer)[0]
    for i in range(len(input_id[0])):
        if input_id[0][i] != new_input_id[i]:
            return []
    first_token = new_input_id[len(input_id[0])]
    at_position = new_input_id.index(732)
    if at_position == len(new_input_id) - 1:
        return []
    next_token = new_input_id[at_position+1]
    return [first_token, next_token, at_position-len(input_id[0]), new_input_id[at_position+1:]]

def chat_prompt_medical(transcript, note):
    prompt = f"""
    You are a clinical expert. Given the transcript : {transcript} #incomplete prompt fix this as well
    """

import csv
with open("../data/challenge_data/clinicalnlp_taskB_test1.csv", encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

mytexts = []
new_entities = []
original_entity = []
for ii, d in enumerate(data):
    

    text = " ".join(d["note"][:2])
    entities_ = []
    entities_ += get_entities(text)
    
    entities = []
    idx_ = []
    for e in entities_:
        if e[1] not in idx_:
            idx_.append(e[1])
            entities.append(e)
    print(entities)

    for e, idx in entities:
        if idx == 0:
                continue
        input_id = chat_change_with_answer(prompt_chat, text[:idx].strip(), tokenizer)
        print(input_id)
        tokens = find_first_and_next_token_for_chat(text, e, idx, input_id)
        print(tokens)
        if not tokens:
                continue
        first_, next_, entity_len, last_id = tokens
        
            
        output = model.generate(torch.tensor(input_id).to(model.device), **generation_config)
        print(output) #a secret tool I will use for later
        values, indices = torch.topk(output.scores[0], k=topk_first_token)
        if first_ in indices[0].tolist():
            continue
        sequences = output.sequences
        for i in range(entity_len+windows):
            output = model.generate(sequences, **generation_config)
            values, indices = torch.topk(output.scores[0], k=topk_next_token)
            if next_ in indices[0].tolist():
                break
            sequences = output.sequences
        if next_ not in indices[0].tolist():
            continue
        new_sequence = sequences[0].tolist()
        new_entity_id = new_sequence[len(input_id[0]):]
        all_new_text_id = input_id[0] + [at_id] + new_entity_id + [at_id] + last_id
        mytext = tokenizer.decode(all_new_text_id).replace("<s>", "").replace("</s>", "")
        new_entity = mytext[mytext.find("@")+1:mytext.rfind("@")].strip().lower()
        if any(ee.strip() in text.lower() for ee in new_entity.split(" ")) or e.lower() in new_entity:
            continue
        mytexts.append(mytext)
        new_entities.append(new_entity)
        original_entity.append((e, idx))
            
    ret = {
            "original_text": text,
            "encounter_id": d["encounter_id"],
            "entities" : entities
        }
