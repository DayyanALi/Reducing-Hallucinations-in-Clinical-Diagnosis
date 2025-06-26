from generator.clients import get_med_llama, get_openai_custom, get_openai_gpt4, get_openai_gpt35
from generator.prompt_template import get_diagnosis_prompt
from generator.output_parsers import  get_diagnosis_StrOutputParser, get_diagnosis_PydanticOutputParser, get_diagnosis_JsonOutputParser
from utils.get_transcript import get_transcript
from dotenv import load_dotenv

load_dotenv()

transcript = get_transcript()
model = get_openai_gpt35()
parser = get_diagnosis_StrOutputParser()
prompt = get_diagnosis_prompt(parser)

# Create a simple diagnosis chain
simple_diagnosis_chain = prompt | model | parser

result = simple_diagnosis_chain.invoke({"transcript":transcript})
print("Original Transcript:",transcript)
print("\n\nGenerated Diagnosis:", result)