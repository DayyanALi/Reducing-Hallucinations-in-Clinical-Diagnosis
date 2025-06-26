DIAGNOSIS_PROMPT_TEMPLATE = """
    You are a clinical assistant.  
    Below is a verbatim transcript of a conversation between a doctor and a patient:

    {transcript}

    Based solely on the transcript above, list the top 5 most likely diagnoses.
    For each diagnosis, give a one-sentence rationale.

    {format_instructions}
"""