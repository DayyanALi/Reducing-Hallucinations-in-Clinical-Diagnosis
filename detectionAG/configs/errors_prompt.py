ERRORS_PROMPT = """
You are a clinical NLP expert.

You are given all transcript facts in the following JSON structure:

{facts_json}

Each fact includes:
- fact_id
- content
- source_text
- and is grouped under a section key (e.g., HPI, ROS, PMH).

Sections can be categorized into one of SOAP categories with these Mapping:**
 - **S (Subjective):** Chief_Complaint, History_of_Present_Illness, Past_Medical_History, Medications, Allergies
 - **O (Objective):** Exam, Labs, Vital Signs, Imaging 
 - **A (Assessment):** Assessment, Diagnosis
 - **P (Plan):** Plan, Medications, Procedures
Your tasks:

1. Review ALL facts and their source_text.
2. Select **10 total facts** that are highly suitable for one of the following clinically important error types. Ensure that there are facts from **each SOAP section**. Error types:
   - Omission
   - Censor Medical Term
   - Censor Value
   - Replace with Similar Medical Term
   - Negation Flip
   - Diagnosis Censor

Suitability rules (must match source_text):
- **Omission**: Applies to any fact.
- **Censor Medical Term**: Only if the text contains specific medical terms, drug names, or disease names.
- **Censor Value**: Only if numbers, dosages, or measurements occur.
- **Replace with Similar Medical Term**: Only if a specific disease, symptom, test, or drug name appears that can be plausibly swapped.
- **Negation Flip**: Only if the text clearly includes negation ("denies", "no", "not") or a positive assertion that can be flipped.
- **Diagnosis Censor**: Only if a diagnosis is explicitly mentioned (e.g., "you have gastroenteritis").

3. For each selected fact:
   - Assign exactly **one** error_type.
   - Produce an **altered_source_text** with the chosen error realistically applied according to these rules:
     - **Omission**: Set altered_source_text = null.
     - **Censor Medical Term**: Delete key medical terms, drug names, disease names or diagnostic terms.
     - **Censor Value**: Remove key numerical values, lab/test results, dosages or measurements.
     - **Replace with Similar Medical Term**: Swap a disease, symptom, test or drug name with a real, similar-sounding medical term (plausible but incorrect).
     - **Negation Flip**: Flip the negation status (e.g., "no fever" -> "fever").
     - **Diagnosis Censor**: EITHER remove the diagnosis name (e.g., "you have [BLANK]") OR remove the entire string (empty string). Randomize between these two options.

Return **only JSON**, with 10 items total, each of the form:

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
"""
