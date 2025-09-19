from pathlib import Path
from typing import Optional
from .cloud_llm import gemini_generate_story

def _try_llama_cpp(model_path: str, prompt: str, max_tokens: int = 700) -> Optional[str]:
    try:
        from llama_cpp import Llama
        llm = Llama(model_path=model_path, n_ctx=4096, n_threads=0, n_gpu_layers=0)
        messages = [
            {"role": "system", "content": "You write imaginative, age-appropriate children's stories."},
            {"role": "user", "content": prompt}
        ]
        out = llm.create_chat_completion(messages=messages, max_tokens=max_tokens, temperature=0.9)
        return out["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

def _fallback_transformers(prompt: str, max_new_tokens: int = 550) -> str:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    sys = "You write imaginative, age-appropriate children's stories."
    chat = f"<|system|>\n{sys}\n<|user|>\n{prompt}\n<|assistant|>\n"
    inputs = tok(chat, return_tensors="pt").to(device)
    out = model.generate(**inputs, do_sample=True, temperature=0.9, top_p=0.9, max_new_tokens=max_new_tokens)
    text = tok.decode(out[0], skip_special_tokens=True)
    return text.split("<|assistant|>")[-1].strip()

def generate_story(user_prompt: str, gguf_path: str | None = None, prefer_cloud: bool = True) -> str:
    txt = gemini_generate_story(user_prompt) if prefer_cloud else None
    if txt:
        return txt
    if gguf_path and Path(gguf_path).exists():
        local = _try_llama_cpp(gguf_path, user_prompt)
        if local:
            return local
    return _fallback_transformers(user_prompt)
