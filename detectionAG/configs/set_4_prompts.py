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

FOLLOW_UP_QS_PROMPT = ChatPromptTemplate.from_template("""
You are a clinical reasoning and diagnostic auditing assistant. 
Your task is to analyze a transcript of a doctor–patient conversation in the context of a specific provisional diagnosis. 

You must identify points where the doctor should have asked additional follow-up questions to:

1. Confirm or refute the provided diagnosis,
2. Differentiate it from close differentials,
3. Increase diagnostic confidence and reduce uncertainty.

Suggest the optimal follow-up question for each point. Be precise and clinically grounded. Avoid vague or compound questions. Each question must be:
• Clinically relevant,
• Answerable directly by the patient,
• Focused on a single piece of information.

For every question:
1. Indicate the **turn_id** from the transcript **after which** the question should have been asked,  
2. Quote the relevant excerpt after which it should have been asked,  
3. Provide a short *reasoning statement* explaining why it’s important and which diagnoses it helps confirm or exclude.

Base your reasoning on:
• Typical and atypical features of the given diagnosis,
• Common differentials with overlapping features,
• Missing details in symptom characterization, risk factors, or review of systems.

Return output strictly in JSON with a main key follow_up_questions, which is a list of objects with keys:
- turn_id
- question
- quoted_excerpt
- reasoning
                                                       
Transcript:
{transcript}

Diagnosis:
{ddx}
"""

)