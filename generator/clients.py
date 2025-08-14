from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from langchain_ollama import OllamaLLM

def openai_gpt4(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4")

def openai_gpt4nano(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4.1-nano-2025-04-14")

def openai_gpt5nano(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-5-nano")

def openai_gpt35(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-3.5-turbo")

def openai_custom(model_name: str="gpt-4", temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name=model_name, temperature=temperature)

def med_llama(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return OllamaLLM(model="medllama2:7b")

def llama3(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return OllamaLLM(model="llama3.2")