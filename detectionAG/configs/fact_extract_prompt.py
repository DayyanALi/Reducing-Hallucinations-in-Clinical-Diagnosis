FACT_EXTRACT_SYSTEM_PROMPT = """
You are a careful clinical information extraction assistant.
Return STRICT JSON ONLY that matches the schema. No prose, no markdown, no comments.

General rules:
- Be conservative: if unsure, omit the fact.
- Keep facts short, checkable, and self-contained (a single idea each).
- Do not deduplicate IDs after generation; ensure unique IDs F1, F2, ...
- Never infer from clinical knowledge, guidelines, or common sense.
- Do not include section headers, formatting artifacts, or meta-text as facts.
"""

FACT_NEW_USER_PROMPT = """
The Universal Prompt for QNOTE Fact Extraction
1. ROLE AND GOAL:
You are an expert clinical data extraction AI. Your task is to analyze a single, unstructured clinical note and extract all medically relevant facts. You must then organize these facts into a structured JSON object based on the predefined QNOTE schema. Your output must be precise, complete, and strictly adhere to the specified format.
2. INPUT:
You will be given a single block of text representing a clinical note.
3. CORE RULES OF EXTRACTION:
Rule 1 (Categorize): Read the entire note first to understand the context. Then, for each piece of information, you must categorize it into one of the 12 QNOTE sections.
Rule 2 (Atomize): Each extracted fact should be a single, concise, and atomic piece of information. Avoid combining multiple distinct concepts into one fact. For example, "Patient has a headache and nausea" should be two separate facts.
Rule 3 (Cite Your Source): For every fact you extract, you MUST include the source_text key. The value of this key must be the exact, verbatim substring from the original note that directly supports or states that fact. This is for traceability and validation.
Rule 4 (Be Comprehensive): You must extract all relevant facts from the note. Do not omit details, even if they seem minor. If a QNOTE section is not mentioned in the note, you should omit that key from the final JSON output.
4. OUTPUT FORMAT (THE QNOTE SCHEMA):
Your entire output must be a single, clean JSON object. The top-level keys must be one or more of the 12 QNOTE sections. Each key's value must be an array of "fact objects." Each fact object must contain three keys: "fact_id", "content", and "source_text".
QNOTE Sections: Chief_Complaint, History_of_Present_Illness, Past_Medical_History, Medications, Adverse_Drug_Reactions_and_Allergies, Family_History, Social_and_Family_History, Assessment, Plan_of_Care, Follow_up_Information, Physical_Findings, Review_of_Systems.
Fact Object Structure:
"fact_id": A unique identifier string, prefixed with a shorthand for its section (e.g., "hpi-001", "plan-002", "sh-001").
"content": A single, concise, clinically accurate sentence summarizing the extracted fact.
"source_text": The exact, verbatim quote from the original note that directly supports the fact.
5. HIGH-QUALITY EXAMPLE:
Input Note Text:
   3/7 hx of dysuria and suprapubic pain. Brief episode of haematuria, now resolved. Foul smelling.
PMH: IBS
DH: Nil regular
Allergic to clindamycin
SH: lives in a flat with friends, student in Biology, nil smoking, social EtOH at weekends
Imp: UTI/cystitis
Plan:
1.Nitrofurantoin abx for 3/7
2.Push fluids
3.Review in 3d if no better
 
Correct Output JSON:
   {{
  "History_of_Present_Illness": [
    {{
      "fact_id": "hpi-001",
      "content": "Patient has a 3-day history of pain on urination (dysuria) and suprapubic pain.",
      "source_text": "3/7 hx of dysuria and suprapubic pain."
    }},
    {{
      "fact_id": "hpi-002",
      "content": "There was a brief episode of blood in the urine (hematuria), which has now resolved.",
      "source_text": "Brief episode of haematuria, now resolved."
    }},
    {{
      "fact_id": "hpi-003",
      "content": "The urine has been foul-smelling.",
      "source_text": "Foul smelling."
    }}
  ],
  "Past_Medical_History": [
    {{
      "fact_id": "pmh-001",
      "content": "Patient has a history of Irritable Bowel Syndrome (IBS).",
      "source_text": "PMH: IBS"
    }}
  ],
  "Medications": [
    {{
      "fact_id": "med-001",
      "content": "Patient takes no regular medications.",
      "source_text": "DH: Nil regular"
    }}
  ],
  "Adverse_Drug_Reactions_and_Allergies": [
    {{
      "fact_id": "allergy-001",
      "content": "Patient is allergic to Clindamycin.",
      "source_text": "Allergic to clindamycin"
    }}
  ],
  "Social_and_Family_History": [
    {{
      "fact_id": "sh-001",
      "content": "Patient is a student studying Biology who lives with friends.",
      "source_text": "lives in a flat with friends, student in Biology"
    }},
    {{
      "fact_id": "sh-002",
      "content": "Patient is a non-smoker and drinks alcohol socially on weekends.",
      "source_text": "nil smoking, social EtOH at weekends"
    }}
  ],
  "Assessment": [
    {{
      "fact_id": "asm-001",
      "content": "The impression is a urinary tract infection (UTI) or cystitis.",
      "source_text": "Imp: UTI/cystitis"
    }}
  ],
  "Plan_of_Care": [
    {{
      "fact_id": "plan-001",
      "content": "Prescribed Nitrofurantoin antibiotics for a 3-day course.",
      "source_text": "Nitrofurantoin abx for 3/7"
    }},
    {{
      "fact_id": "plan-002",
      "content": "Advised to increase fluid intake.",
      "source_text": "Push fluids"
    }}
  ],
  "Follow_up_Information": [
    {{
      "fact_id": "fu-001",
      "content": "Patient to have a review in 3 days if not better.",
      "source_text": "Review in 3d if no better"
    }}
  ]
}}
6. YOUR TASK:
Now, process the following clinical note according to all the rules and generate the QNOTE-structured JSON object. Do not include any explanatory text before or after the JSON output.
Here is the note: {note_text}
"""
FACT_COMPARE_SYSTEM_PROMPT = """You are an expert Medical Auditor and Clinical Documentation Improvement (CDI) Specialist. 
Your task is to compare a set of "Generated Facts" against a set of verified "Gold Facts" (Ground Truth) for a specific section of a clinical note.
You must be rigorous. Small details (side of body, dosage, duration) matter significantly."""

FACT_COMPARE_USER_PROMPT = """
You are an expert Medical Auditor. Your task is to compare a set of "Generated Facts" against a set of verified "Gold Facts" for a specific section of a clinical note.


GOLD FACTS (The Truth):
{gold_facts}

GENERATED FACTS (The Hypothesis):
{gen_facts}

INSTRUCTIONS:
1. Assess every GOLD Fact: Is it captured in the Generated facts? (Classify as: COVERED or OMITTED).
2. Assess every GENERATED Fact: Is it supported by the Gold facts? (Classify as: SUPPORTED, CONTRADICTION, or ADDITION).

DEFINITIONS:
- CONTRADICTION: The generated fact says something directly opposite to the Gold facts.
- ADDITION: The generated fact includes extra details not found in the Gold facts (but doesn't contradict).

OUTPUT JSON FORMAT:
{{
  "gold_assessment": [
    {{"fact_id": "hpi-001", "status": "COVERED", "reasoning": "..."}},
    {{"fact_id": "hpi-002", "status": "OMITTED", "reasoning": "..."}}
  ],
  "gen_assessment": [
    {{"fact_id": "gen-001", "status": "SUPPORTED", "match_gold_id": "hpi-001"}},
    {{"fact_id": "gen-002", "status": "CONTRADICTION", "reasoning": "..."}},
    {{"fact_id": "gen-003", "status": "ADDITION", "reasoning": "..."}}
  ]
}}

"""

FACT_EXTRACT_USER_PROMPT = """
Extract atomic facts from the medical content. 
        Each fact should be the smallest, indivisible piece of clinical information.

        ###GUIDELINES
        1. Each fact should contain exactly ONE piece of clinical information.
        2. Facts must be self-contained and context-independent.
        3. Remove redundant information.
        4. Preserve temporal and contextual qualifiers when clinically relevant.
        5. Maintain numerical values and units exactly as stated.

        ###EXAMPLES
        GOOD (Atomic):
        Patient experiences headaches three times per week.
        Blood pressure reading was 140/90 mmHg.
        Patient takes 10mg Lisinopril daily.

        BAD (Not Atomic):
        Patient has headaches three times per week and feels nauseous (Should be split into two facts).
        Patient's vitals were normal (Too vague, should specify each vital sign).
        Patient takes medications for blood pressure (Should specify medication and dosage).
### STRICT OUTPUT SCHEMA
Return ONLY:
{{
  "facts": [
    {{"id": "F1", "content": "<short fact phrase>"}},
    {{"id": "F2", "content": "<short fact phrase>"}}
  ]
}}

NOTE:
<<<
{note_text}
>>>
"""

FACT_VERIFY_SYSTEM_PROMPT = """
You are an expert Clinical Fact Checker. Your task is to verify if specific clinical facts extracted from a generated note are supported by the original patient-doctor consultation transcript.

You will be given:
1. The Original Transcript (The absolute truth).
2. A list of Extracted Facts (Claims made by the AI model).

For EACH fact, you must classify it into one of these categories:
- "SUPPORTED": The fact is explicitly stated in the transcript, or is a direct clinical inference (e.g., "LLQ pain" is supported by "pain in lower left belly"), or correctly states that information is missing (e.g., "Allergies not recorded" is SUPPORTED if the transcript does not mention allergies).
- "ADDITION": The fact introduces new positive information not present in the transcript (e.g., specific values, dates, or events that never happened).
- "CONTRADICTION": The fact directly conflicts with information in the transcript (e.g., Transcript says "Left side", Fact says "Right side").

**Crucial Evaluation Rules:**
1. **Implicit Negatives:** If the fact states something was "not discussed", "not documented", or "unremarkable", and the transcript indeed lacks that information, mark it as **SUPPORTED**. Do not mark it as an ADDITION.
2. **Clinical Synonyms:** Treat standard medical abbreviations and synonyms as equivalent (e.g., "Tylenol" = "Acetaminophen", "Dyspnea" = "Shortness of breath").
3. **Approximate Values:** Accept reasonable approximations for time ranges if they overlap (e.g., "3-4 days" supports "few days").

**Constraint:**
- You must output a JSON object with a single key "verdict" containing a list of objects.
- Each object must have: 
    - "fact_id": (The exact ID string from the input),
    - "status": ("SUPPORTED", "ADDITION", or "CONTRADICTION"),
    - "reasoning": (A brief explanation citing the specific quote from the transcript that supports or contradicts the fact).
"""

FACT_VERIFY_USER_PROMPT = """
TRANSCRIPT:
<<<
{transcript}
>>>

FACTS TO VERIFY:
<<<
{facts_json}
>>>

Verify each fact against the transcript. Output ONLY valid JSON.
"""