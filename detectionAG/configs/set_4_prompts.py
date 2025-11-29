# prompts.py

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 🧩 QUESTION PROMPT
QUESTION_PROMPT = ChatPromptTemplate.from_template("""
You are a clinical assistant. Based on the transcript and the differential diagnosis below, first extract all known key facts 
(e.g., age, presenting symptoms, relevant history, medications). 
Then identify any missing or unclear items and generate follow-up questions grouped into:

- red_flags
- clarifications
- history_meds_social

Return your output strictly in JSON with keys:
red_flags, clarifications, history_meds_social, priority_order.

Transcript:
{transcript}

Differential Diagnosis:
{ddx}
""")

# 🩺 DIFFERENTIAL DIAGNOSIS PROMPT
DDX_PROMPT = ChatPromptTemplate.from_template("""
You are a diagnostic reasoning assistant using the provided patient transcript and follow-up questions to generate a structured differential diagnosis. Follow this exact methodology step by step: 

Step 1: **Extract and summarize key clinical elements** from the transcript in bullet points. 
Include:
- Chief complaint 
- Symptoms (onset, duration, severity, aggravating/alleviating factors) 
- Past medical history 
- Medications/allergies 
- Family/social history 
- Vital signs/exam findings 
- Labs/imaging (if mentioned)

Step 2: **Generate differentials using the VINDICATE mnemonic.**  
For each relevant category, list 1–3 possible diagnoses that could explain the findings. Provide a brief rationale linking to transcript evidence.  
Mnemonic:
- V: Vascular (e.g., blockages, clots, bleeds)
- I: Infectious/Inflammatory (e.g., infections, inflammation)
- N: Neoplastic (e.g., cancers, tumors)
- D: Degenerative/Deficiency (e.g., wear-and-tear, nutrient lacks)
- I2: Iatrogenic/Intoxication (e.g., drug side effects, toxins)
- C: Congenital (e.g., birth defects)
- A: Autoimmune/Allergic (e.g., immune attacks, allergies)
- T: Traumatic (e.g., injuries)
- E: Endocrine/Metabolic (e.g., hormone or metabolism issues)

Step 3: **Rank the top 3–5 most likely differentials** based on transcript details. 
For each, assign:
- A likelihood (High / Medium / Low)
- An explanation that summarizes reasoning

Step 4: **Identify supporting and opposing evidence** from the transcript for each top diagnosis:
- *Supporting evidence:* Findings that make this diagnosis more likely.
- *Opposing evidence:* Findings that argue against this diagnosis.

Output in structured JSON:
{{
  "step1_summary": "...",
  "step2_vindicate": {{
    "V": ["Diagnosis1: Rationale..."],
    "I": [],
    "N": [],
    "D": [],
    "I2": [],
    "C": [],
    "A": [],
    "T": [],
    "E": []
  }},
  "step3_ranked_ddx": [
    {{
      "diagnosis": "...",
      "likelihood": "...",
      "explanation": "...",
      "supporting_evidence": ["..."],
      "opposing_evidence": ["..."]
    }}
  ]
}}

Transcript:
{transcript}

Questions:
{questions}
""")


# 🧾 NOTE GENERATION PROMPT
NOTE_PROMPT = ChatPromptTemplate.from_template("""
You are a medical scribe. Create a structured SOAP note (Subjective, Objective, Assessment, Plan) based on:

Transcript:
{transcript}

Follow-up Questions:
{questions}

Differential Diagnoses:
{ddx}

Return output strictly in JSON with keys:
S, O, A, P, ICD10_candidates, followups.

Do not invent vitals or examination findings — write “Not recorded” when absent.
""")

# 🩹 BASELINE NOTE PROMPT
BASELINE_NOTE_PROMPT = ChatPromptTemplate.from_template("""
You are a medical AI scribe. Convert the transcript into a concise SOAP note directly.

Transcript:
{transcript}
""")
