HALLUCINATION_SYSTEM_PROMPT = """
    You compare two fact lists and return STRICT JSON only. No prose.
"""
HALLUCINATION_USER_PROMPT = """
Given BASELINE_FACTS and CANDIDATE_FACTS (each as a list of {"id","content"}), find all candidate facts
that are NOT supported by any baseline fact (allow small paraphrase matches).
- If a candidate fact is unsupported or contradicted by baseline, flag it as a factual hallucination.
Return only the hallucinated candidate facts (id + content), no others.

Return JSON:
{
  "hallucinations": [
    {"id":"<candidate_id>", "content":"<candidate_content>"},
    ...
  ]
}

BASELINE_FACTS:
{baseline_json}

CANDIDATE_FACTS:
{candidate_json}
"""