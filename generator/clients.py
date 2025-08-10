from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaLLM, OllamaEmbeddings

def openai_gpt4(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4", temperature=temperature)

def openai_gpt4nano(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4.1-nano-2025-04-14", temperature=temperature)

def openai_gpt5nano(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-5-nano")

def openai_gpt35(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-3.5-turbo", temperature=temperature)

def openai_custom(model_name: str="gpt-4", temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name=model_name, temperature=temperature)

def med_llama(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return OllamaLLM(model="medllama2:7b", temperature=temperature)

def llama3(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return OllamaLLM(model="llama3.2", temperature=temperature)

def gemini_pro(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=temperature)

def embedding_model_llama() -> HuggingFacePipeline:
    return OllamaEmbeddings(model="nomic-embed-text:latest")