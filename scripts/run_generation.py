from generator.clients import openai_gpt35, med_llama, llama3, openai_gpt4mini
from generator.prompt_template import get_diagnosis_prompt, get_judge_prompt
from generator.output_parsers import get_StrOutputParser, get_diagnoses_JsonOutputParser, get_diagnosis_PydanticOutputParser
from hallucination.detection.detect import ContextualDetector, ConsistencyDetector
from utils.utils import get_transcript
from dotenv import load_dotenv
import ast
import json
load_dotenv()

transcript = get_transcript()
Diagnosis_model = openai_gpt4mini()

diagnoses_parser = get_diagnoses_JsonOutputParser()
diagnosis_prompt = get_diagnosis_prompt(diagnoses_parser)
simple_diagnosis_chain = diagnosis_prompt | Diagnosis_model | diagnoses_parser
result = simple_diagnosis_chain.invoke({"transcript": transcript})

detection_model = openai_gpt4mini()
detect = ContextualDetector(detection_model)

hallucination_results = detect(transcript=transcript, diag_and_rationale=result["diagnoses"])
print("\n\nHallucination Results:", hallucination_results)
