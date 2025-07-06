from generator.clients import get_openai_gpt35
from generator.prompt_template import get_diagnosis_prompt, get_judge_prompt
from generator.output_parsers import get_diagnosis_StrOutputParser
from utils.get_transcript import get_transcript
from dotenv import load_dotenv

load_dotenv()

transcript = get_transcript()
Diagnosis_model = get_openai_gpt35()
Judge_model = get_openai_gpt35()

parser = get_diagnosis_StrOutputParser()
diagnosis_prompt = get_diagnosis_prompt(parser)
judge_prompt = get_judge_prompt(parser)

simple_diagnosis_chain = diagnosis_prompt | Diagnosis_model | parser
result = simple_diagnosis_chain.invoke({"transcript": transcript})

judge_chain = judge_prompt | Judge_model | parser
hallucination_analysis = judge_chain.invoke({"transcript": transcript, "output": result})

# === Output
print("Original Transcript:", transcript)
print("\n\nGenerated Diagnosis:", result)
print("\n\nHallucination Analysis:", hallucination_analysis)
