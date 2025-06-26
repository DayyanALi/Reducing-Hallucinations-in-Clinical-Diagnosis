from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline, HuggingFaceEndpoint
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

def get_openai_gpt4(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4")

def get_openai_gpt35(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-3.5-turbo-0125")

def get_openai_custom(model_name: str="gpt-4", temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name=model_name, temperature=temperature)

def get_med_llama(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    model = pipeline(
        task="text-generation",
        model="medalpaca/medalpaca-7b",
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )
    return HuggingFacePipeline(pipeline=model)
