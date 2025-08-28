from langchain.schema.runnable import RunnableLambda
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from generator.clients import llama3_2_hd

model = llama3_2_hd(max_new_tokens=50)

result = model.invoke("complete this sentence: an apple a day keeps the")

print("Generated Answer:", result["text"])
print("Output tokens:", result["output_tokens"])
print("Output hidden states shape (last layer):", result["output_hidden_states"][0].shape)
