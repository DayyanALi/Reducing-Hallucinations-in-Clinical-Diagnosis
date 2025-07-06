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
