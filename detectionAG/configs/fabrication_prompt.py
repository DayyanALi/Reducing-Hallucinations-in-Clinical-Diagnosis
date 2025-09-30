FABRICATION_SYSTEM_PROMPT = """
    You are a clinical plausibility checker. Return STRICT JSON only. No prose.
"""

FABRICATION_USER_PROMPT = """
Given CANDIDATE_FACTS (list of {"id","content"}), flag facts that are medically impossible or implausible
(e.g., nonsensical vitals/labs, impossible doses, contradictions like giving penicillin despite penicillin allergy if stated).
Be conservative: if unclear, do not flag.

Return JSON:
{
  "fabrications": [
    {"id":"<candidate_id>", "content":"<candidate_content>", "reason":"<short why>"},
    ...
  ]
}

CANDIDATE_FACTS:
{candidate_json}
"""