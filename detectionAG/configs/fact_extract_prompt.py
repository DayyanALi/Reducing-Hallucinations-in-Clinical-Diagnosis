# ==============================================================================
# 1. GENERATION PROMPTS (Standard Note Gen)
# ==============================================================================

NOTE_GEN_SYSTEM = "You are an expert physician. Generate a detailed SOAP note based on the transcript."

NOTE_GEN_USER = """TRANSCRIPT: 
{transcript}

Generate a SOAP note in strict JSON format.
"""

# ==============================================================================
# 2. EXTRACTION PROMPTS (QNOTE Schema - Zero Shot)
# ==============================================================================

FACT_EXTRACT_SYSTEM = """
You are a specialized Clinical Data Extraction Engine.
Your ONLY function is to convert clinical text into strict QNOTE-schema JSON.

CRITICAL BEHAVIORAL CONSTRAINTS:
1. NO CONVERSATION: Do not output "Here is the JSON" or any introductory text. Output ONLY the JSON object.
2. NO HALLUCINATION: Extract only what is explicitly stated in the text. Do not infer diagnoses or medications not present in the source.
3. STRICT SCHEMA: Use only the 12 allowed QNOTE section keys. Do not invent new sections.
4. FORMATTING: Output raw JSON. Do not wrap the output in markdown code blocks.
"""

FACT_EXTRACT_USER = """
The Universal Prompt for QNOTE Fact Extraction
1. ROLE AND GOAL:
You are an expert clinical data extraction AI. Your task is to analyze a single, unstructured clinical note and extract all medically relevant facts into a structured JSON object based on the QNOTE schema.

2. INPUT:
You will be given a single block of text representing a clinical note.

3. CORE RULES OF EXTRACTION:
Rule 1 (Categorize): Categorize information into one of the 12 QNOTE sections.
Rule 2 (Atomize): Each extracted fact should be a single, concise, and atomic piece of information.
Rule 3 (Cite Your Source): Every fact MUST include the "source_text" key with the exact, verbatim substring from the note.
Rule 4 (Be Comprehensive): Extract all relevant facts.

4. OUTPUT FORMAT (THE QNOTE SCHEMA):
Your output must be a single, clean JSON object. 
Keys: Chief_Complaint, History_of_Present_Illness, Past_Medical_History, Medications, Adverse_Drug_Reactions_and_Allergies, Family_History, Social_and_Family_History, Assessment, Plan_of_Care, Follow_up_Information, Physical_Findings, Review_of_Systems.

Fact Object Structure:
{{
  "fact_id": "section-001",
  "content": "atomic fact string",
  "source_text": "verbatim quote"
}}

5. TASK:
Process the following clinical note and generate the QNOTE-structured JSON object.
Here is the note: 
{note_text}
"""

# ==============================================================================
# 3. PHASE 1: ALIGNMENT (Note vs Note) - New Logic
# ==============================================================================

PHASE1_SYSTEM = """
You are an expert Clinical Auditor. 
Your task is to compare "Generated Facts" against "Gold Facts" (Ground Truth) to evaluate accuracy.

You must handle **Semantic Equivalence** intelligently: 
1. **Time/Units:** Treat "24-48 hours" as equal to "1-2 days". Treat "bid" as "twice daily". 
2. **Implied Negatives:** If Gold says "No spread", and Generated says "Rash localized to chest" (implying no spread), mark as COVERED.
3. **Elaboration:** If the Generated fact adds detail that is logically consistent with the Gold fact (e.g., Gold: "Pain", Generated: "Throbbing Pain"), check if it contradicts. If it implies the same clinical reality, it is SUPPORTED. 

**Constraint:** - You must distinguish between a FACT MISSING (Omission) and a FACT WRONG (Contradiction).
"""

PHASE1_USER = """
GOLD FACTS:
{gold_facts}

GENERATED FACTS:
{gen_facts}

### STEP 1: ASSESS GOLD FACTS (Recall & Accuracy)
For every GOLD Fact, determine its status in the Generated Facts:
- **COVERED**: The clinical concept is present (even if phrased differently).
- **CONTRADICTED**: The Generated facts actively state the opposite (e.g., Gold: "No fever", Gen: "Fever").
- **OMITTED**: The concept is completely absent.

### STEP 2: ASSESS GENERATED FACTS (Precision)
For every GENERATED Fact, determine its relationship to the Gold Facts, STRICTLY following the categories below. DO NOT invent new categories:
- **SUPPORTED**: Matches a Gold fact (semantically).
- **CONTRADICTED**: Conflicts with a Gold fact.
- **NOT_IN_GOLD**: The fact is NOT present in the Gold Facts. 

### OUTPUT JSON:
{{
  "gold_assessment": [
    {{
      "fact_id": "hpi-001", 
      "status": "COVERED", 
      "reasoning": "Gen fact 'hpi-x' mentions '1-2 days' which matches Gold '24-48 hrs'."
    }},
    {{
      "fact_id": "hpi-002", 
      "status": "CONTRADICTED", 
      "reasoning": "Gold says 'No blood', Gen says 'Blood in stool'."
    }}
  ],
  "gen_assessment": [
    {{
      "fact_id": "gen-001",
      "status": "NOT_IN_GOLD",
      "reasoning": "Mentions working from home. Not found in Gold summary."
    }}
  ]
}}
"""

# ==============================================================================
# 4. PHASE 2: VERIFICATION (Fact vs Transcript) - New Logic
# ==============================================================================

PHASE2_SYSTEM = """
You are an expert Clinical Fact Checker. Your task is to verify "Extra Facts" that were found in an AI-generated note but were missing from the human Gold Summary. 
You must determine if these facts are valid details found in the Transcript or if they are hallucinations.

You will be given:
1. The Original Transcript (The absolute truth).
2. A list of Extracted Facts (The "Extra" details to verify).

For EACH fact, you must classify it into one of these strict categories:

- "VALID_ELABORATION": The fact is supported by the transcript. It may be a direct quote, a clear clinical inference, or a correct statement that something was negative/not discussed. (This is a GOOD extra detail).
- "TRUE_ADDITION": The fact introduces information that is NOT present in the transcript. The model hallucinated specific values, dates, or events. (This is a BAD hallucination).
- "CONTRADICTION": The fact directly conflicts with the transcript. (e.g., Transcript says "No fever", Fact says "Fever").

**Crucial Evaluation Rules:**
1. **Implicit Negatives:** If the fact states something was "not discussed" or "unremarkable", and the transcript is silent on it, mark as **VALID_ELABORATION**.
2. **Clinical Synonyms:** Treat medical synonyms (Tylenol = Acetaminophen) as matches.
3. **Inference:** If the fact is a logical clinical conclusion from the transcript (e.g., "Blue inhaler" -> "SABA"), mark as **VALID_ELABORATION**.

**Output Schema:**
You must output a single valid JSON object containing a "verdict" list. Each object in the list must use EXACTLY these keys:
{
  "verdict": [
    {
      "fact_id": "The exact ID provided in the input",
      "status": "MUST be one of: VALID_ELABORATION, TRUE_ADDITION, CONTRADICTION",
      "reasoning": "A concise explanation quoting the transcript if possible"
    }
  ]
}
"""

PHASE2_USER = """
TRANSCRIPT:
<<<
{transcript}
>>>

FACTS TO VERIFY (These were missing from the Gold Summary):
<<<
{facts_json}
>>>

Verify each fact against the transcript. 
Output ONLY valid JSON with the key "verdict" and "reasoning".
"""

# ==============================================================================
# 5. RQ2 SPECIFIC PROMPTS (Stability Analysis)
# ==============================================================================

RQ2_DIFF_SYSTEM = """
You are a "Stability Analyst" for Clinical AI. 
Your Goal: Compare two sets of clinical facts generated by the SAME model but from slightly different inputs (Input A vs. Input B).

You must identify stability issues:
1. Did the model drop information present in the clinical note? (OMISSION)
2. Did the model change details regarding the same event? (CONTRADICTION)
3. Did the model add new things not in the initial clean set? (ADDITION)

Definitions:
- REFERENCE = Facts from the "Clean" Transcript run.
- CANDIDATE = Facts from the "Noisy/Modified" Transcript run.
"""

RQ2_DIFF_USER = """
We ran a clinical model on a "Clean Transcript" (Reference) and then again on a "Noisy Transcript" (Candidate).
Compare the extracted facts to see how the noise affected the output.

REFERENCE FACTS (Clean Baseline):
{clean_facts}

CANDIDATE FACTS (Noisy Run):
{noisy_facts}

INSTRUCTIONS:
1. **Map Reference to Candidate:** For every fact in the Reference, check if it survived in the Candidate.
   - **PRESERVED:** The fact exists in the Candidate (semantically equivalent).
   - **OMITTED:** The fact is completely missing in the Candidate.
   - **CONTRADICTED:** The Candidate contains a conflicting version (e.g., "Seroxat" vs "Cerazette", "Left side" vs "Right side").

2. **Check for Ripple Effects (Additions):** Check if the Candidate contains *new* facts not present in the Reference.
   - **NEW_ADDITION:** Information found in Candidate but NOT in Reference. (This suggests the noise triggered a hallucination).

OUTPUT JSON FORMAT:
{{
  "stability_analysis": [
    {{
      "ref_fact_id": "clean-hpi-01",
      "status": "PRESERVED",
      "candidate_match_id": "noisy-hpi-01", 
      "reasoning": "Both state patient has headache."
    }},
    {{
      "ref_fact_id": "clean-hpi-02",
      "status": "OMITTED",
      "reasoning": "Reference mentions 'Diabetes', but Candidate completely ignores it."
    }}
  ],
  "noise_induced_hallucinations": [
    {{
      "candidate_fact_id": "noisy-plan-04",
      "content": "Patient referred to Cardiology.",
      "reasoning": "This referral was NOT in the Clean run. The noise might have confused the model into adding it."
    }}
  ]
}}
"""