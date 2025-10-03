HALLUCINATION_SYSTEM_PROMPT = """
You are a strict fact checker. 
Your task is to compare two fact lists and return only the candidate facts that are unsupported or contradicted by the baseline.
Return STRICT JSON only, no prose.
"""


HALLUCINATION_USER_PROMPT = """
You are given BASELINE_FACTS and CANDIDATE_FACTS, each a list of {{\"id\",\"content\"}} objects.

Check each candidate fact:
- If the same information (allowing small paraphrase or synonym) exists in the baseline facts, it is supported → DO NOT FLAG.
- If the candidate fact is not present in the baseline OR contradicts a baseline fact, flag it as a factual hallucination.

Return JSON with schema:
{{
  "hallucinations": [
    {{"id":"<candidate_id>", "content":"<candidate_content>"}},
    ...
  ]
}}

BASELINE_FACTS:
{baseline_json}

CANDIDATE_FACTS:
{candidate_json}
"""
