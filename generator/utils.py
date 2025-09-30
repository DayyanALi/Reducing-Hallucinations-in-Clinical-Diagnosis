from transformers import LlamaForCausalLM, LlamaTokenizer, AutoModelForCausalLM, AutoTokenizer, AutoConfig
import torch

def get_model(model_type, model_family, max_new_tokens=1):
    if model_family == "opt":
        if model_type == "7b":
            model_path = "facebook/opt-6.7b"
        else:
            model_path = "facebook/opt-13b"
        at_id = [787, 1039]
    elif model_family == "llamabase":
        model_path = f"meta-llama/Llama-2-{model_type}-hf"
    elif model_family == "bloom":
        model_path = "bigscience/bloom-7b1"
        at_id = [2566, 35]
    elif model_family == "falcon":
        at_id = 0
        model_path = f"tiiuae/falcon-{model_type}"
    elif model_family == "gptj":
        model_path = "EleutherAI/gpt-j-6b"
        at_id = 2488
    elif model_family == "mpt":
        model_path = "mosaicml/mpt-7b"
        at_id = [1214, 33]
    elif model_family == "vicuna":
        model_path = f"lmsys/vicuna-{model_type}-v1.5"
        at_id = 732
    else:
        model_path = f"meta-llama/Llama-2-{model_type}-chat-hf"
        
    if "llama" in model_family:
        model = LlamaForCausalLM.from_pretrained(
            model_path,
            load_in_8bit=False,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            device_map='auto')
        tokenizer = LlamaTokenizer.from_pretrained(model_path)
        at_id = 732
    elif "baichuan" in model_family:
        tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left", trust_remote_code=True)
        tokenizer.pad_token_id = 0 if tokenizer.pad_token_id is None else tokenizer.pad_token_id # set as the <unk> token
        if tokenizer.pad_token_id == 64000:
            tokenizer.pad_token_id = 0 # for baichuan model (need fix)
        config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_path, config=config, torch_dtype=torch.float32, trust_remote_code=True, low_cpu_mem_usage=True, device_map="auto")
        at_id = [3757, 92952]
    elif "mpt" in model_family:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            load_in_8bit=False,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            device_map='auto')
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            load_in_8bit=False,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            device_map='auto')
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
    if model_family == "falcon" or model_family == "gptj":
        generation_config = dict(
                            top_k=0,
                            top_p=1.0,
                            do_sample=False,
                            num_beams=1,
                            max_new_tokens=max_new_tokens,
                            return_dict_in_generate=True,
                            output_hidden_states=True,
                            output_scores = True,
                            eos_token_id=tokenizer.eos_token_id,
                            pad_token_id=tokenizer.eos_token_id
                        )
    else:
        generation_config = dict(
                            top_k=0,
                            top_p=1.0,
                            do_sample=False,
                            num_beams=1,
                            max_new_tokens=max_new_tokens,
                            return_dict_in_generate=True,
                            output_hidden_states=True,
                            output_scores = True
                        )
        
    return model, tokenizer, generation_config, at_id

# import torch
# import torch.nn.functional as F

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

SPECIAL_TAGS = [B_INST, E_INST, "<<SYS>>", "<</SYS>>"]

def chat_change(dialog,
        tokenizer):
    prompt_tokens = []
    unsafe_requests = []
    
    unsafe_requests.append(
        any([tag in msg["content"] for tag in SPECIAL_TAGS for msg in dialog])
    )
    assert all([msg["role"] == "user" for msg in dialog[::2]]) and all(
        [msg["role"] == "assistant" for msg in dialog[1::2]]
    ), (
        "model only supports 'system', 'user' and 'assistant' roles, "
        "starting with 'system', then 'user' and alternating (u/a/u/a/u...)"
    )
    # print(dialog)
    dialog_tokens = sum(
        [
            tokenizer.encode(
                f"{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} ",
            ) + [2]
            for prompt, answer in zip(
                dialog[::2],
                dialog[1::2],
            )
        ],
        [],
    )
    assert (
        dialog[-1]["role"] == "user"
    ), f"Last message must be from user, got {dialog[-1]['role']}"
    dialog_tokens += tokenizer.encode(
        f"{B_INST} {(dialog[-1]['content']).strip()} {E_INST}",
    )
    prompt_tokens.append(dialog_tokens)
    return prompt_tokens

def chat_change_with_answer(dialog, answer_,
        tokenizer):
    prompt_tokens = []
    unsafe_requests = []
    unsafe_requests.append(
        any([tag in msg["content"] for tag in SPECIAL_TAGS for msg in dialog])
    )
    assert all([msg["role"] == "user" for msg in dialog[::2]]) and all(
        [msg["role"] == "assistant" for msg in dialog[1::2]]
    ), (
        "model only supports 'system', 'user' and 'assistant' roles, "
        "starting with 'system', then 'user' and alternating (u/a/u/a/u...)"
    )
    # print(dialog)
    dialog_tokens = sum(
        [
            tokenizer.encode(
                f"{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} ",
            ) + [2]
            for prompt, answer in zip(
                dialog[::2],
                dialog[1::2],
            )
        ],
        [],
    )
    assert (
        dialog[-1]["role"] == "user"
    ), f"Last message must be from user, got {dialog[-1]['role']}"
    dialog_tokens += tokenizer.encode(
        f"{B_INST} {(dialog[-1]['content']).strip()} {E_INST} {answer_.strip()}",
    )
    prompt_tokens.append(dialog_tokens)
    return prompt_tokens

def generate_output(model_family, model, tokenizer, config, text, answer=None):
    if "chat" not in model_family:
        assert answer is None
        input_id = tokenizer(text.strip(), return_tensors='pt')['input_ids'].tolist()
    else:
        if answer is None:
            input_id = chat_change([{"role": "user", "content": text.strip()}], tokenizer)
        else:
            input_id = chat_change_with_answer([{"role": "user", "content": text.strip()}], answer.strip(), tokenizer)
    output = model.generate(torch.tensor(input_id).to(model.device), **config)
    return output


def get_pe(logit, id_, start_at):
    probabilities = F.softmax(logit, dim=2)
    log_probabilities = torch.log(probabilities)
    entropy = -probabilities * log_probabilities
    entropy_sum = torch.sum(entropy, dim=-1)

    pl = []
    el = []
    for i, idx in enumerate(id_[1:]):
        if i < start_at - 1:
            continue
        pl.append(probabilities[0][i][idx].item())
        el.append(entropy_sum[0][i].item())
    return pl, el