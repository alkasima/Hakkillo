import os
import threading

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from hakkillo.settings import BASE_MODEL, BASE_REVISION, DEFAULT_ADAPTER, SYSTEM_PROMPT


def configure_cpu(threads=None):
    count = threads or int(os.environ.get("HAKKILLO_THREADS", min(4, os.cpu_count() or 1)))
    if count < 1:
        raise ValueError("CPU thread count must be positive")
    torch.set_num_threads(count)


def load_base():
    configure_cpu()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, revision=BASE_REVISION, dtype=torch.float32,
        use_safetensors=True, attn_implementation="sdpa",
    ).to("cpu")
    return model, tokenizer


def adapter_source():
    remote = os.environ.get("HAKKILLO_ADAPTER", "").strip()
    if remote:
        return remote
    if (DEFAULT_ADAPTER / "adapter_config.json").exists():
        return str(DEFAULT_ADAPTER)
    return None


def generate_reply(model, tokenizer, message, history=None, max_new_tokens=96, temperature=0.0, repetition_penalty=1.08):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Enter a message first")
    if len(message) > 4000:
        raise ValueError("Please keep your message under 4,000 characters")
    max_new_tokens = max(1, min(int(max_new_tokens), 256))
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in (history or [])[-8:]:
        if entry.get("role") in {"user", "assistant"} and isinstance(entry.get("content"), str):
            messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": message})
    while True:
        ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=False)
        if ids.shape[1] <= 1024:
            break
        if len(messages) <= 2:
            raise ValueError("Your message is too long for this CPU demo; please shorten it")
        del messages[1]
    options = {"max_new_tokens": max_new_tokens, "do_sample": temperature > 0,
               "pad_token_id": tokenizer.pad_token_id, "eos_token_id": tokenizer.eos_token_id,
               "repetition_penalty": float(repetition_penalty)}
    if temperature > 0:
        options.update(temperature=float(temperature), top_p=0.9)
    with torch.inference_mode():
        output = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), **options)
    return tokenizer.decode(output[0, ids.shape[1]:], skip_special_tokens=True).strip()


class Assistant:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.lock = threading.Lock()

    def reply(self, message, history, max_new_tokens=96, temperature=0.0):
        with self.lock:
            if self.model is None:
                model, tokenizer = load_base()
                source = adapter_source()
                if source:
                    model = PeftModel.from_pretrained(
                        model, source, revision=os.environ.get("HAKKILLO_ADAPTER_REVISION") or None
                    )
                self.model, self.tokenizer = model.eval(), tokenizer
            return generate_reply(self.model, self.tokenizer, message, history, max_new_tokens, temperature)
