from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from langchain_ollama import OllamaLLM
from langchain.schema.runnable import RunnableLambda
from transformers import AutoTokenizer, AutoModelForCausalLM
from utils.utils import get_hidden_states

def openai_gpt4(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4")

def openai_gpt4mini(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-4.1-nano-2025-04-14")

def openai_gpt35(temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name="gpt-3.5-turbo")

def openai_custom(model_name: str="gpt-4", temperature: float=0.0) -> ChatOpenAI:
    return ChatOpenAI(model_name=model_name, temperature=temperature)

def med_llama(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return OllamaLLM(model="medllama2:7b")

def llama3(max_new_tokens: int=1024, temperature: float=0.0) -> HuggingFacePipeline:
    return OllamaLLM(model="llama3.2")

def llama3_2_hd(max_new_tokens: int=1024, temperature: float=0.0, device:str="cpu") -> HuggingFacePipeline:
    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-3.2-1B",
        output_hidden_states=True
    ).to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
    
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    def _fn(prompt: str):
        return get_hidden_states(
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            device=device
        )

    runnable = RunnableLambda(_fn)
    return runnable

