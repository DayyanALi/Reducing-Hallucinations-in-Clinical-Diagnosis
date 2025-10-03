OMISSION_SYSTEM_PROMPT = """
You are a strict omission detector.
Your task is to identify clinically important baseline facts that are missing in the candidate facts.
Return STRICT JSON only, no prose.
"""

OMISSION_USER_PROMPT = """
You are given BASELINE_FACTS and CANDIDATE_FACTS, each a list of {{\"id\",\"content\"}} objects.

Check each baseline fact:
- If the same information (allowing small paraphrase or synonym) exists in the candidate facts, it is supported → DO NOT FLAG.
- If the baseline fact is not present in the candidate, and it is clinically important, flag it as a critical omission.

Clinically important = allergies, red-flag symptoms (e.g., chest pain, shortness of breath), key positives/negatives, vital signs, critical diagnoses, and essential plans.

Return JSON with schema:
{{
  "critical_omissions": [
    {{"id":"<baseline_id>", "content":"<baseline_content>"}},
    ...
  ]
}}

BASELINE_FACTS:
{baseline_json}

CANDIDATE_FACTS:
{candidate_json}
"""
