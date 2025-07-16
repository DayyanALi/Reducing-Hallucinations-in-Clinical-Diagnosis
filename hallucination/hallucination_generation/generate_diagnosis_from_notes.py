import json
from typing import List, Dict
from dotenv import load_dotenv

from langchain import LLMChain, PromptTemplate
from generator.clients import get_openai_gpt4
from generator.output_parsers import get_StrOutputParser
from generator.templates import DIAGNOSIS_FROM_NOTES_TEMPLATE

load_dotenv()

with open("data/challenge_data/train.json") as f:
    obj = json.load(f)
records: List[Dict] = obj["data"]

llm = get_openai_gpt4()
parser = get_StrOutputParser()
DIAG_PROMPT = PromptTemplate(
    input_variables=["note"],
    template=DIAGNOSIS_FROM_NOTES_TEMPLATE
)
chain = DIAG_PROMPT | llm | parser

augmented = []
for rec in records:
    note = rec["tgt"]   
    
    raw = chain.invoke({"note": note})
    
    try:
        diag_and_rationale = json.loads(raw)
    except json.JSONDecodeError:
        obj = json.loads(raw)
        diag_and_rationale = [obj]
    
    # attach
    new_rec = dict(rec)
    new_rec["diag_and_rationale"] = diag_and_rationale
    print("new rec", new_rec)
    augmented.append(new_rec)

out_path = "data/challenge_data/train_with_diagnoses.json"
with open(out_path, "w") as f:
    json.dump({"data": augmented}, f, indent=2)

print(f"✅ Wrote {len(augmented)} records to {out_path}")
