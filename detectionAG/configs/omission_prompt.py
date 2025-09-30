OMISSION_SYSTEM_PROMPT = """
   "You detect important missing items. Return STRICT JSON only. No prose.
"""

OMISSION_USER_PROMPT = """
Given BASELINE_FACTS and CANDIDATE_FACTS, list clinically important baseline items that are missing in candidate.
Focus on high-salience: allergies, red-flag symptoms (e.g., chest pain, shortness of breath), key positives/negatives,
vital signs, critical diagnoses, and essential plans.

Return JSON:
{
  "critical_omissions": [
    {"id":"<baseline_id>", "content":"<baseline_content>", "why":"<short why it matters>"},
    ...
  ]
}

BASELINE_FACTS:
{baseline_json}

CANDIDATE_FACTS:
{candidate_json}
"""