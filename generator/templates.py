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
INJECT_CONTEXTUAL_HALLUCINATION_DIAGNOSES_TEMPLATE = """
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

INJECT_CONSISTENCY_HALLUCINATION_DIAGNOSES_TEMPLATE = """
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


INJECT_CONTEXTUAL_HALLUCINATION_NOTES_TEMPLATE = """
You are an expert clinical scribe whose job is to take a fully written doctor–patient transcript and its corresponding clinical note, then introduce one or more **contextual hallucinations** into the **Assessment & Plan** section—while leaving every other part of the note verbatim.  

## Your task in detail:
1. **Read** the entire doctor–patient transcript (ground truth).  
2. **Read** the complete clinical note, including all sections (Chief Complaint, HPI, ROS, Physical Exam, Results, and Assessment & Plan).  
3. **Select** the **Assessment & Plan** section for modification.  
4. **Introduce** at least one new hallucinated plan sentence or item into that section.  
5. **Do not** change any text or formatting in the other sections of the note.  
6. **Return** the **entire clinical note** (all sections), with your hallucinated addition(s) embedded in the Assessment & Plan.

## Constraints on your hallucinated content:
- It must be **medically plausible** and **factually correct** in general (e.g., a real diagnostic test or specialist referral).  
- It must be **related** to one of the patient’s problems (e.g., CHF, hypertension, depression, or preventive care).  
- It must **not** contradict or conflict with any detail in the transcript—only add unsupported plan items.  
- It must match the original style and tone of the Assessment & Plan section.

## Examples of contextual hallucinations you might introduce (but not limited to these):
- “Order a morning serum creatinine and electrolyte panel two weeks after diuretic initiation to monitor renal function.”  
- “Refer to sleep medicine for overnight oximetry to evaluate for sleep apnea.”  
- “Recommend enrollment in a supervised cardiac rehabilitation program three times per week for structured exercise monitoring.”  
- “Schedule a telehealth visit in 48 hours to review home blood pressure logs and adjust therapy as needed.”  
- “Arrange a transthoracic echocardiogram with contrast to better characterize her valvular function.”

## Input Variables
- **transcript**: The full doctor–patient conversation.  
- **clinical note**: The entire clinical note corresponding to that transcript.

## Output
Return the **complete** clinical note text, with hallucinated content added only in the Assessment & Plan section. Do **not** output anything else.

## Example
** transcript:
[doctor] hi , martha . how are you ?\n[patient] i'm doing okay . how are you ?\n
[doctor] i'm doing okay . so , i know the nurse told you about dax . i'd like to tell dax a little bit about you , okay ?\n[patient] okay .\n
[doctor] martha is a 50-year-old female with a past medical history significant for congestive heart failure , depression and hypertension who presents for her annual exam . so , martha , it's been a year since i've seen you . how are you doing ?\n
[patient] i'm doing well . i've been traveling a lot recently since things have , have gotten a bit lighter . and i got my , my vaccine , so i feel safer about traveling . i've been doing a lot of hiking . uh , went to washington last weekend to hike in northern cascades, like around the mount baker area .\n
[doctor] nice . that's great . i'm glad to hear that you're staying active , you know . i , i just love this weather . i'm so happy the summer is over . i'm definitely more of a fall person .\n[patient] yes , fall foliage is the best .\n
[doctor] yeah . um , so tell me , how are you doing with the congestive heart failure ? how are you doing watching your diet ? i know we've talked about watching a low sodium diet . are you doing okay with that ?\n
[patient] i've been doing well with that . i resisted , as much , as i could , from the tater tots , you know , the soft pretzels , the salty foods that i , i love to eat . and i've been doing a really good job .\n
[doctor] okay , all right . well , i'm glad to hear that . and you're taking your medication ?\n[patient] yes .\n[doctor] okay , good . and any symptoms like chest pains , shortness of breath , any swelling in your legs ?\n[patient] no , not that i've noticed .\n
[doctor] okay , all right . and then in terms of your depression , i know that we tried to stay off of medication in the past because you're on medications for your other problems . how are you doing ? and i know that you enrolled into therapy . is that helping ? or-\n
[patient] yeah , it's been helping a lot . i've been going every week , um , for the past year since my last annual exam . and that's been really helpful for me .\n
[doctor] okay . so , no , no issues , no feelings of wanting to harm yourself or hurt others ?\n[patient] no , nothing like that .\n[doctor] okay , all right . and then in terms of your high blood pressure , i know that you and i have kind of battled in the past with you remembering to take some of your blood pressure medications . how are you doing with that ?\n
[patient] i'm still forgetting to take my blood pressure medication . and i've noticed when work gets more stressful , my blood pressure goes up .\n[doctor] okay . and , and so how has work going for you ?\n
[patient] it's been okay . it's been a lot of long hours , late nights . a lot of , um , you know , fiscal year end data that i've been having to pull . so , a lot of responsibility , which is good . but with the responsibility comes the stress .\n
[doctor] yeah , okay , all right . i understand . um , all right . well , i know that you did a review of system sheet when you checked in with the nurse . i know that you were endorsing some nasal congestion from some of the fall pollen and allergies . any other symptoms , nausea or vomiting , abdominal pain , anything like that ?\n[patient] no , nothing like that .\n
[doctor] no , okay , all right . well , i'm gon na go ahead and do a quick physical exam , okay ?\n[patient] okay .\n[doctor] hey , dragon , show me the blood pressure . so , yeah , looking at your blood pressure today here in the office , it is a little elevated . you know , it could just , you could just be nervous . uh , let's look at some of the past readings . hey , dragon , show me the blood pressure readings . hey , dragon , show me the blood pressure readings . here we go . uh , so they are running on the higher side . um , y- you know , i , i do think that , you know , i'd like to see you take your medication a little bit more , so that we can get that under control a little bit better , okay ?\n[patient] okay .\n
[doctor] so , i'm just gon na check out your heart and your lungs . and you know , let you know what i find , okay ?\n[patient] okay .\n[doctor] okay . so , on your physical examination , you know , everything looks good . on your heart exam , i do appreciate a three out of six systolic ejection murmur , which i've heard in the past , okay ? and on your lower extremities , i do appreciate one plus pitting edema , so you do have a little bit of fluid in your legs , okay ?\n
[patient] okay .\n[doctor] let's go ahead , i wan na look at some of your results , okay ? hey , dragon , show me the echocardiogram . so , this is the result of the echocardiogram that we did last year . it showed that you have that low-ish pumping function of your heart at about 45 % . and it also sh- shows some mitral regurgitation , that's that heart murmur that i heard , okay ?\n
[doctor] um , hey , dragon , show me the lipid panel . so , looking at your lipid panel from last year , you know , everything , your cholesterol was like , a tiny bit high . but it was n't too , too bad , so i know you're trying to watch your diet . so , we'll repeat another one this year , okay ?\n[patient] okay .\n
[doctor] um , so i wan na just go over a little bit about my assessment and my plan for you , okay ? so , for your first problem your congestive heart failure , um , i wan na continue you on your current medications . but i do wan na increase your lisinopril to 40 milligrams a day , just because your blood pressure's high . and you know , you are retaining a little bit of fluid . i also wan na start you on some lasix , you know , 20 milligrams a day . and have you continue to watch your , your diet , okay ?\n
[patient] okay .\n[doctor] i also wan na repeat another echocardiogram , okay ?\n[patient] all right .\n[doctor] hey , dragon , order an echocardiogram . from a depression standpoint , it sounds like you're doing really well with that . so , i'm , i'm really happy for you . i'm , i'm glad to see that you're in therapy and you're doing really well . i do n't feel the need to start you on any medications this year , unless you feel differently .\n[patient] no , i feel the same way .\n
[doctor] okay , all right . and then for your last problem your hypertension , you know , again i , i , i think it's out of control . but we'll see , i think , you know , i'd like to see you take the lisinopril as directed , okay ? uh , i want you to record your blood pressures within the patient , you know , take your blood pressure every day . record them to me for like , about a week , so i have to see if we have to add another agent , okay ? 'cause we need to get that under better control for your heart failure to be more successful , okay ?\n
[patient] okay .\n[doctor] do you have any questions ? , and i forgot . for your annual exam , you're due for a mammogram , so we have to schedule for that , as well , okay ?\n[patient] okay .\n
[doctor] okay . do you have any questions ?\n[patient] can i take all my pills at the same time ?\n[doctor] yeah .\n[patient] 'cause i've been trying to take them at different times of the day , 'cause i did n't know if it was bad to take them all at once or i should separate them . i do n't know .\n
[doctor] yeah . you can certainly take them , you know , all at the same time , as long , as yeah , they're all one scale . you can take them all at the same time . just set an alarm-\n[patient] okay .\n
[doctor] . some time during the day to take them , okay ?\n[patient] that might help me remember better .\n[doctor] all right . that sounds good . all right , well , it's good to see you .\n[patient] good seeing you too .\n
[doctor] hey , dragon , finalize the note .",
** clinical note:
CHIEF COMPLAINT\n\nAnnual exam.\n\nHISTORY OF PRESENT ILLNESS\n\nMartha Collins is a 50-year-old female with a past medical history significant for congestive heart failure, depression, and hypertension who presents for her annual exam. It has been a year since I last saw the patient.\n\nThe patient has been traveling a lot recently since things have gotten a bit better. She reports that she got her COVID-19 vaccine so she feels safer about traveling. She has been doing a lot of hiking.\n\nShe reports that she is staying active. She has continued watching her diet and she is doing well with that. The patient states that she is avoiding salty foods that she likes to eat. She has continued utilizing her medications. The patient denies any chest pain, shortness of breath, or swelling in her legs.\n\nRegarding her depression, she reports that she has been going to therapy every week for the past year. This has been really helpful for her. She denies suicidal or homicidal ideation.\n\nThe patient reports that she is still forgetting to take her blood pressure medication. She has noticed that when work gets more stressful, her blood pressure goes up. She reports that work has been going okay, but it has been a lot of long hours lately.\n\nShe endorses some nasal congestion from some of the fall allergies. She denies any other symptoms of nausea, vomiting, abdominal pain.\n\nREVIEW OF SYSTEMS\n\n\u2022 Ears, Nose, Mouth and Throat: Endorses nasal congestion from allergies.\n\u2022 Cardiovascular: Denies chest pain or dyspnea on exertion.\n\u2022 Respiratory: Denies shortness of breath.\n\u2022 Gastrointestinal: Denies abdominal pain, nausea, or vomiting.\n\u2022 Psychiatric: Endorses depression. Denies suicidal or homicidal ideations.\n\nPHYSICAL EXAMINATION\n\n\u2022 Cardiovascular: Grade 3/6 systolic ejection murmur.\n1+ pitting edema of the bilateral lower extremities.\n\nVITALS REVIEWED\n\n\u2022 Blood Pressure: Elevated.\n\nRESULTS\n\nEchocardiogram demonstrates decreased ejection fraction of 45%. Mitral regurgitation is present.\n\nLipid panel: Elevated cholesterol.\n\n
ASSESSMENT AND PLAN

Martha Collins is a 50-year-old female with a past medical history significant for congestive heart failure, depression, and hypertension who presents for her annual exam.

**Congestive heart failure.**  
- Medical Reasoning: She has been compliant with her medication and dietary modifications. Her previous year’s echocardiogram demonstrated a reduced ejection fraction of 45%, as well as some mitral regurgitation. Her cholesterol levels were slightly elevated on her lipid panel from last year.  
- Additional Testing: We will order a repeat echocardiogram. We will also repeat a lipid panel this year.  
- Medical Treatment: She will continue with her current medications. We will increase her lisinopril to 40 mg daily and initiate furosemide (Lasix) 20 mg daily.  
- Patient Education and Counseling: I encouraged her to continue with dietary modifications.

**Depression.**  
- Medical Reasoning: She is doing well with weekly therapy.  
- Medical Treatment: No medication changes at this time.

**Hypertension.**  
- Medical Reasoning: She has been compliant with dietary modifications but inconsistent with her lisinopril, which correlates with stress-related blood pressure elevations.  
- Medical Treatment: As above, increase lisinopril to 40 mg daily.  
- Patient Education and Counseling: Continue to monitor home blood pressures daily for one week and report back.

**Healthcare maintenance.**  
- Medical Reasoning: She is overdue for her routine mammogram.  
- Additional Testing: We will schedule a screening mammogram.
- Patient Education and Counseling: We will refer her to a sleep medicine specialist to obtain overnight oximetry for possible undiagnosed sleep apnea.

Patient Agreements: The patient understands and agrees with the recommended medical treatment plan.\n",

The final line (“We will refer her to a sleep medicine specialist…”) clearly adds a new plan item that is not supported by any mention of sleep symptoms in the transcript, yet does not contradict anything (the patient’s sleep was never discussed).

Now let's incorporate this contextual hallucination into the assessment and plan section of the clinical note.

---
**Transcript:**  
\"\"\"  
{transcript}  
\"\"\"  

**Clinical Note:**  
\"\"\"  
{note}  
\"\"\"  
Proceed now to introduce your contextual hallucination(s) into the Assessment & Plan and return the full note.
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
