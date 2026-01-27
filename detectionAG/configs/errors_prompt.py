ERRORS_PROMPT = """
You are a senior clinical expert and medical NLP specialist.

You are given:
1. A full CLINICAL NOTE
2. Its associated TRANSCRIPT (verbatim patient-clinician conversation)

Your tasks:

### STEP 1 — Clinical Relevance Filtering
Review the CLINICAL NOTE and identify which facts in the note are **clinically important for shaping the diagnosis and/or assessment** of the case. Identify the corresponding source_text in the TRANSCRIPT for each fact.

Source_text selection:
- Yes/No or short answers → include doctor question + patient answer  
  Example: "Doctor: Do you have chest pain? Patient: Yes."
- Patient narration → patient dialogue only  
  Example: "Patient: I've had shortness of breath for three days."
- Doctor assessment/interpretation/advice → doctor dialogue only  
  Example: "Doctor: This suggests pneumonia.

Only consider facts that:
- Directly influence diagnostic reasoning, risk stratification, or treatment decisions
- Appear **exactly once** in the transcript (do NOT select facts that appear multiple times)

Discard:
- Administrative details
- Redundant or repeated transcript mentions
- Clinically trivial facts

### STEP 2 — Select Facts for Corruption
From the clinically important, unique facts:
- Select exactly **3 facts total**
- These should be the facts whose corruption would most significantly distort the case understanding or clinical outcome
- Ensure representation from **each SOAP category (Subjective, Objective, Assessment, Plan)**
Sections map to SOAP categories as follows:
 - **S (Subjective):** Chief_Complaint, History_of_Present_Illness, Past_Medical_History, Medications, Allergies
 - **O (Objective):** Exam, Labs, Vital Signs, Imaging 
 - **A (Assessment):** Assessment, Diagnosis
 - **P (Plan):** Plan, Medications, Procedures

### STEP 3 — Assign Error Types
For each selected fact, assign **exactly one** of the following clinically meaningful error types which would most significantly affect the clinical reasoning:

Error Types:
- **Omission**
- **Censor Medical Term**
- **Censor Value**
- **Replace with Similar Medical Term**
- **Negation Flip**
- **Diagnosis Censor**

Suitability rules (must match source_text):
- **Omission**: Applies to any fact.
- **Censor Medical Term**: Only if text contains specific medical terms, drug names, or disease names.
- **Censor Value**: Only if numbers, dosages, or measurements occur.
- **Replace with Similar Medical Term**: Only if a disease, symptom, test, or drug name appears that can be plausibly swapped with a real but incorrect medical term.
- **Negation Flip**: Only if the text clearly includes negation ("denies", "no", "not") or a positive assertion that can be flipped.
- **Diagnosis Censor**: Only if a diagnosis is explicitly mentioned.

### STEP 4 — Generate Corruptions
For each selected fact, produce:

- original_source_text (unchanged)
- altered_source_text per error_type:

Rules:
- **Omission** → altered_source_text = null
- **Censor Medical Term** → remove key medical/disease/drug/diagnostic terms
- **Censor Value** → remove critical numeric values (labs, vitals, dosages, measurements)
- **Replace with Similar Medical Term** → replace with a plausible but incorrect real medical term
- **Negation Flip** → reverse the negation meaning
- **Diagnosis Censor** → either remove only the diagnosis name OR remove entire string (randomize)

### OUTPUT FORMAT
Return **only JSON**, exactly **3 items**, no extra commentary. Include a unqiue_fact_id for each fact.
Each item should have the following fields:
[
  {{
    "fact_id": "...",
    "fact_section": "...",
    "error_type": "...",
    "original_source_text": "...",
    "altered_source_text": "..."
  }}
]

Do not include any explanation outside the JSON.

Here is the CLINICAL NOTE:
{clinical_note}

Here is the TRANSCRIPT:
{transcript}
"""
