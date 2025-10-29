# prompts.py

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 🧩 QUESTION PROMPT
QUESTION_PROMPT = ChatPromptTemplate.from_template("""
You are a clinical assistant. Based on the transcript below, first extract all known key facts 
(e.g., age, presenting symptoms, relevant history, medications). 
Then identify any missing or unclear items and generate follow-up questions grouped into:

- red_flags
- clarifications
- history_meds_social

Return your output strictly in JSON with keys:
red_flags, clarifications, history_meds_social, priority_order.

Transcript:
{transcript}
""")

# 🩺 DIFFERENTIAL DIAGNOSIS PROMPT
DDX_PROMPT = ChatPromptTemplate.from_template("""
You are a diagnostic reasoning assistant.
Given the transcript and follow-up questions, produce 3–5 possible differential diagnoses.

For each diagnosis, include:
- dx
- likelihood: (low / moderate / high)
- evidence_for: list of supporting quotes from transcript
- evidence_against: list if applicable
- next_steps: investigations or management suggestions

Transcript:
{transcript}

Questions:
{questions}
""")

# 🧾 NOTE GENERATION PROMPT
NOTE_PROMPT = ChatPromptTemplate.from_template("""
You are a medical scribe. Create a structured SOAP note (Subjective, Objective, Assessment, Plan) based on:

Transcript:
{transcript}

Follow-up Questions:
{questions}

Differential Diagnoses:
{ddx}

Return output strictly in JSON with keys:
S, O, A, P, ICD10_candidates, followups.

Do not invent vitals or examination findings — write “Not recorded” when absent.
""")

# 🩹 BASELINE NOTE PROMPT
BASELINE_NOTE_PROMPT = ChatPromptTemplate.from_template("""
You are a medical AI scribe. Convert the transcript into a concise SOAP note directly.

Transcript:
{transcript}
""")
