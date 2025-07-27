DIAGNOSIS_PROMPT_TEMPLATE = """
    You are a clinical assistant.  
    Below is a verbatim transcript of a conversation between a doctor and a patient:

    {transcript}

    Based solely on the transcript above, list the top 3 most likely diagnoses.
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
You are a clinical assistant helping to validate AI‐generated medical reasoning.  Below you will see:

1. A doctor–patient transcript—every detail here is the ground truth.
2. A single diagnosis that an AI model has proposed.
3. A concise, one‐sentence rationale explaining that diagnosis.

Your goal is to **append exactly one new sentence** to the rationale that:

• Is **medically plausible** and **clearly related** to the given diagnosis.  
• Is **not supported** by *any* information in the transcript (i.e., it introduces an unsupported detail).  
• **Does not contradict** or conflict with the transcript; it merely adds new, ungrounded content.  
• Matches the style and tone of the existing rationale.  
• Stands on its own as a single, coherent sentence.

---  
**Transcript**  
\"\"\"  
{transcript}  
\"\"\"  

**Diagnosis**  
\"\"\"  
{original_diagnosis}  
\"\"\"  

**Rationale**  
\"\"\"  
{original_rationale}  
\"\"\"  

---  
**Instruction**  
Append one extra sentence meeting the criteria above.  
**Output**  
Return the whole new rationale that includes the original rationale and the extra sentence specified above.
"""

INJECT_CONSISTENCY_HALLUCINATION_TEMPLATE = """
You are a clinical assistant helping to evaluate the reasoning quality of AI-generated medical explanations.  
Below you will see:

1. A doctor–patient transcript—every detail here is the **ground truth**.
2. A diagnosis that an AI model has proposed.
3. A rationale that explains why the diagnosis was given.

Your task is to rewrite the rationale so that it **sounds medically plausible**, but contains a **logical inconsistency** in relation to the diagnosis.

This inconsistency could take one of the following forms:
- It introduces symptoms or findings that contradict the diagnosis.
- It draws conclusions that don't logically follow from the diagnosis.
- It creates internal contradictions (e.g., stating mutually exclusive facts).
- It emphasizes reasoning that applies to a different diagnosis.

The hallucinated rationale should:
• Be **grammatically correct** and **medically plausible**.  
• Contain **at least one clinical inconsistency** (logical, semantic, or diagnostic).  
• Remain in the **style and tone** of the original rationale.  
• Not be obviously absurd or obviously wrong—aim for **subtle and realistic flaws**.

---  
**Transcript**  
\"\"\"  
{transcript}  
\"\"\"  

**Diagnosis**  
\"\"\"  
{original_diagnosis}  
\"\"\"  

**Original Rationale**  
\"\"\"  
{original_rationale}  
\"\"\"  

---  
**Instruction**  
Rewrite the rationale so that it sounds reasonable at first glance but contains a **flawed or inconsistent reasoning step**, as described above.

**Output**  
Return only the rewritten rationale.
"""


# ================================================================================================================================================================
# ================================================================================================================================================================
# ================================================================================================================================================================

DETECT_CONTEXTUAL_HALLUCINATION_TEMPLATE = """
You are a clinical fact‑checker. Your job is to identify **contextual hallucinations** in a one‑sentence rationale for a proposed diagnosis. A contextual hallucination is any detail that sounds plausible but is **not supported** by the doctor–patient transcript.

Always think step by step before answering, and return **only** “Yes” (if you spot any unsupported detail) or “No” (if the rationale is fully grounded).

-----  
**Example**  
Transcript (full dialogue):  
\"\"\"  
"dialogue": "[doctor] and why is she here ? annual exam . okay . all right . hi , sarah . how are you ?
\n[patient] good . how are you ?\n[doctor] i'm good . are you ready to get started ?\n[patient] yes , i am .
\n[doctor] okay . so sarah is a 27-year-old female here for her annual visit . so , sarah , how have you been since the last time i saw you ?
\n[patient] i've been doing better . um , i've been struggling with my depression , um , a bit more just because we've been trapped really inside and remotely over the past year , so i've been struggling , um , off and on with that .
\n[doctor] okay . uh , and from looking at the notes , it looks like we've had you on , uh , prozac 20 milligrams a day .
\n[patient] yes .\n[doctor] are , are you taking that ?\n[patient] i am taking it . i think it's just a lot has been weighing on me lately .
\n[doctor] okay . um , and do you feel like you need an increase in your dose , or do you ... what are you thinking ? do you think that you just need to deal with some stress or you wan na try a , a different , uh , medication or ...
\n[patient] i think the , the medication has helped me in the past , and maybe just increasing the dose might help me through this patch .
\n[doctor] okay . all right . and , and what else has been going on with you ? i know that you've had this chronic back pain that we've been dealing with . how's that , how's that going ?
\n[patient] uh , i've been managing it . it's still , um , here nor there . just , just keeps , um , it really bothers me when i sit for long periods of time at , at my desk at work . so i have ... it helps when i get up and move , but it gets really stiff and it hurts when i sit down for long periods of time .
\n[doctor] okay , and do you get any numbing or tingling down your legs or any pain down leg versus the other ?
\n[patient] a little bit of numbing , but nothing tingling or hurting down my legs .
\n[doctor] okay , and does the , um , do those symptoms improve when you stand up or change position ?\n[patient] yeah , it does .
\n[doctor] okay . all right . and any weakness in , in your legs ?\n[patient] no , no weakness , just , just the weird numbing . like , it's , like , almost like it's falling asleep on me .
\n[doctor] okay . and are you able to , um , do your activities of daily living ? do you exercise , go to the store , that type of thing ?
\n[patient] yeah , i am . it bothers me when i'm on my feet for too long and sitting too long , just the extremes of each end .
\n[doctor] okay . and i know that you've had a coronary artery bypass grafting at the young age of 27 , so how's that going ?
\n[patient] yeah , i had con- i had a congenital ... you know , i had a congenital artery when i was a baby , so , um , they had to do a cabg on me , um , fairly young in life , but i've been ... my heart's been doing , doing well , and arteries have been looking good .
\n[doctor] okay . all right , well , let's go ahead and do a quick physical exam . um , so looking at you , you do n't appear in any distress . um , your neck , there's no thyroid enlargement . uh , your heart i hear a three out of six , systolic ejection murmur , uh , that's stable . your lungs otherwise sound clear . your abdomen is soft , and you do have some pain to palpation of your lumbar spine . uh , and you've had decreased flexion of your back . uh , your lower extremity strength is good , and there's no edema . so let's go ahead and look at some of your results . hey , dragon , show me the ecg . okay , so that looks basically unchanged from last year , which is really good . hey , dragon , show me the lumbar spine x-ray . hey , dragon , show me the back x-ray . great . so this looks good . that's also stable from last year . okay . so let's go ahead and , you know , my , my plan for you at this time , you know , from a chronic back pain standpoint , if you need , um , you know , some more physical therapy , and i can refer you to physical therapy to help with those symptoms that are kind of lingering .
\n[patient] mm-hmm .\n[doctor] um , and we can always give you some pain medication if you , if you get some pain periodically with activity . how do you feel about that ? do you need some pain medication ?
\n[patient] no , i think physical therapy is the right way to , way to start out on this .\n[doctor] okay . hey , dragon , order physical therapy referral . and then in terms of your depression , we talked about increasing your prozac , so we'll increase it from 20 milligrams to 40 milligrams . it's just one tablet once a day .\n[patient] okay .
\n[doctor] um , and i'll send those to your pharmacy . does that sound okay ?\n[patient] that sounds great .\n[doctor] hey , dragon , order prozac , 40 milligrams , once a day . and then in terms of your ... the heart bypass that you've had ... let's go ahead and just order another echocardiogram for you , and i wan na continue you on the aspirin for now , okay ?
\n[patient] okay .\n[doctor] hey , dragon , order an echocardiogram . hey , dragon , order aspirin 81 milligrams daily . okay , so the nurse will come in . she'll help you schedule those things , and we'll go from there , okay ?
\n[patient] okay .\n[doctor] all right , take care .\n[patient] thank you .\n[doctor] hey , dragon , finalize the note .\n"\"\"\"  

Diagnosis:  
\"\"\"  
Major Depressive Disorder  
\"\"\"  

Rationale:  
\"\"\"  
The patient reports feelings of depression that have worsened recently, and is already treated with Prozac 20 mg, which she believes needs an adjustment. The patient might also benefit from a referral to a psychologist for cognitive behavioral therapy in conjunction with medication.  
\"\"\"  

**Step‑by‑step logic**  
1. **Supported**: Worsened depression and desire for a higher Prozac dose are documented.  
2. **Unsupported**: The transcript never mentions referral to a psychologist or CBT.  

→ **Answer:** Yes

Diagnosis:
\"\"\"  
Chronic Lower Back Pain
\"\"\"  

Rationale:
\"\"\"  
Patient has reported continual discomfort and stiffness when performing routine activities and prolonged sitting, associated with mild numbness in legs.
\"\"\"  

**Step-by-step logic**
1. The patient complains of back pain that “really bothers me when I sit for long periods,” and describes “a little bit of numbing” but no tingling or weakness.

-> **Answer:** No

-----  
**Now evaluate this case:**  
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

Let’s think step by step. Return exactly one word: **Yes** or **No**.
"""


# ================================================================================================================================================================
# ================================================================================================================================================================
# ================================================================================================================================================================

DETECT_CONSISTENCY_HALLUCINATION_TEMPLATE = """
You are a clinical fact‑checker tasked with identifying **consistency hallucinations**—cases where a one‑sentence rationale for a proposed diagnosis **directly contradicts** or **conflicts with** information in the doctor–patient transcript.

Below you will see:

  1. The full transcript (“Ground Truth”).  
  2. A single proposed diagnosis.  
  3. Its one‑sentence rationale.

Example 1 (consistent):
  Transcript: “Patient denies any chest pain or shortness of breath.”
  Diagnosis: “Angina”
  Rationale: “Although she denies chest pain, her risk factors still warrant evaluation for angina.”
  → Answer: No

Example 2 (inconsistent):
  Transcript: “Patient denies any chest pain or shortness of breath.”
  Diagnosis: “Angina”
  Rationale: “Severe chest pain on exertion is classic for angina in this patient.”
  → Answer: Yes

Now evaluate the case below. If the rationale **directly contradicts** any statement in the transcript, answer **Yes**; otherwise, answer **No**.

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

**Return exactly one word: Yes or No.**
"""
