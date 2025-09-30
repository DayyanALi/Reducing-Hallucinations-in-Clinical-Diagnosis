FACT_EXTRACT_SYSTEM_PROMPT = """
You are a careful clinical information extraction assistant. 
Return STRICT JSON ONLY with the schema provided. No explanations.
"""

FACT_EXTRACT_USER_PROMPT = """
Extract ONLY explicit clinical facts from the NOTE below.
- Keep each fact short and checkable (e.g., "denies chest pain", "HR 110 bpm", "took ibuprofen", "penicillin allergy").
- DO NOT infer beyond the text. No guidelines or common-sense additions.
- Create unique ids: F1, F2, F3, ...
Return JSON with schema:
{
  "facts": [
    {"id": "F1", "content": "<short fact phrase>"},
    ...
  ]
}

NOTE:
<<<
{note_text}
>>>
"""
