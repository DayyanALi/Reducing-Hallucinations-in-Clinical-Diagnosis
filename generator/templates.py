DIAGNOSIS_PROMPT_TEMPLATE = """
    You are a clinical assistant.  
    Below is a verbatim transcript of a conversation between a doctor and a patient:

    {transcript}

    Based solely on the transcript above, list the top 5 most likely diagnoses.
    For each diagnosis, give a one-sentence rationale.

    {format_instructions}
"""

DIAGNOSIS_JUDGE_TEMPLATE = """
You are a clinical hallucination auditor.

Your task is to assess whether the generated diagnoses below contain any hallucinations when compared to the doctor–patient transcript.

Here is the transcript:

{transcript}

Here is the generated diagnosis output (from another model):

{output}

Evaluate the diagnosis based on the following hallucination types:

1. **Factual Hallucination** — Are there any incorrect or misleading clinical facts in the output?
2. **Input-Conflicting Hallucination** — Does the output contradict anything said in the transcript?
3. **Fabricated Source or Procedure** — Does the output refer to a guideline, procedure, or study that was not mentioned in the transcript?
4. **Outdated Reference** — Does the output rely on obsolete or outdated medical guidance?
5. **Spurious Correlation or Reasoning Error** — Does the output make medically unjustified leaps or link symptoms to conclusions without basis?

Respond for each type with **"Yes" or "No"**, followed by a one-line rationale.

{format_instructions}
"""

DECOMPOSE_PROMPT = """\
You are a clinical assistant.  Break the following rationale into a numbered list of atomic sub-claims.
Output only the JSON list of strings.

Rationale:
\"\"\"
{rationale}
\"\"\"
"""


ATTEST_PROMPT = """\
You are a clinical NLI assistant. Given a patient transcript and a claim, do two things:
1) Quote the exact sentence(s) from the transcript that support or contradict the claim (or write NONE).
2) Label the claim as one of: ENTAILED, NEUTRAL, or CONTRADICTED.

Respond in JSON:
{{
  "claim": "{claim}",
  "evidence": "{evidence}",
  "label": "{label}"
}}
Transcript:
\"\"\"
{transcript}
\"\"\"
"""

# Template to make diagnosis from clinical notes, which would be used in the hallucination generation process
DIAGNOSIS_FROM_NOTES_TEMPLATE = """
You are a skilled clinical assistant.  Given the following clinical summary, 
generate **up to 3** most plausible diagnoses along with 
a concise rationale for each, in this exact JSON format:

[
  {{
    "diagnosis": "<Disease or condition name>",
    "rationale": "<One-sentence clinical reasoning justifying this diagnosis>"
  }},
  ...
]

Transcript:
\"\"\"
{note}
\"\"\"
"""

#  Template to inject Contextual Hallucination in diagnosis-rationale
INJECT_CONTEXTUAL_HALLUCINATION_TEMPLATE = """
You are a clinical assistant.  Below is a doctor–patient transcript, one of the model’s generated diagnoses, and its one-sentence rationale:

Transcript:
\"\"\"
{transcript}
\"\"\"

Diagnosis:
\"\"\"
{diagnosis}
\"\"\"

Rationale:
\"\"\"
{rationale}
\"\"\"

Your task: Inject **one** new, medical‑sounding sentence that is related to the diagnosis but **directly contradicts or conflicts** either the rationale above or a fact in the transcript.
– Keep it concise and in the same style.  
– Return **only** that one contradictory sentence.
"""
