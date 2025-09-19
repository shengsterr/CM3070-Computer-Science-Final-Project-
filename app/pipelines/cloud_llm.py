import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def gemini_generate_story(prompt: str, model_name: str = "gemini-1.5-flash") -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        system = "You write imaginative, age-appropriate children's stories."
        resp = model.generate_content([{"role": "user", "parts": [system + "\n\n" + prompt]}])
        return (resp.text or "").strip()
    except Exception:
        return None
