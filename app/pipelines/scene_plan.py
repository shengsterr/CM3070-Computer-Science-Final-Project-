# app/pipelines/scene_plan.py
import json, re
from typing import List, Dict, Optional
from .cloud_llm import gemini_generate_story

JSON_HINT = """Return ONLY a JSON array like:
[
  {"caption": "1–2 short sentences a child can read.", "image_prompt": "visual description for an illustration"},
  ...
]"""

def _extract_json_array(text: str) -> Optional[list]:
    # Try fenced code block
    m = re.search(r"```json\s*(\[.*?\])\s*```", text, flags=re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Try first [...] block
    m = re.search(r"(\[.*\])", text, flags=re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None

def _fallback_naive(story: str, num_scenes: int) -> List[Dict]:
    paras = [p.strip() for p in story.split("\n\n") if p.strip()]
    if not paras:
        paras = [story.strip()]
    scenes = []
    for i, para in enumerate(paras[:num_scenes], 1):
        # 1–2 sentences
        bits = re.split(r"(?<=[.!?])\s+", para)
        cap = " ".join(bits[:2]).strip()
        if not cap:
            cap = para[:160]
        scenes.append({
            "caption": cap,
            "image_prompt": f"children's picture book, soft watercolor, bright and friendly. Depict: {cap}. No text on image."
        })
    return scenes

def plan_scenes(story_text: str, num_scenes: int = 6, prefer_cloud: bool = True) -> List[Dict]:
    """
    Returns a list of dicts: [{"caption": str, "image_prompt": str}, ...]
    """
    if prefer_cloud:
        prompt = (
            "Split the following children's story into clear visual scenes.\n"
            f"Create exactly {num_scenes} scenes.\n"
            "Each scene needs:\n"
            "- caption: 1–2 short, simple sentences a child can read\n"
            "- image_prompt: a concise visual description (no text overlay), children's picture-book watercolor style\n\n"
            f"{JSON_HINT}\n\n"
            f"Story:\n---\n{story_text}\n---"
        )
        txt = gemini_generate_story(prompt)
        if txt:
            arr = _extract_json_array(txt)
            if isinstance(arr, list) and arr:
                # Ensure required keys exist
                cleaned = []
                for item in arr[:num_scenes]:
                    cap = (item.get("caption") or "").strip()
                    ip  = (item.get("image_prompt") or "").strip()
                    if not cap:
                        continue
                    if not ip:
                        ip = f"children's picture book, soft watercolor, bright and friendly. Depict: {cap}. No text on image."
                    cleaned.append({"caption": cap, "image_prompt": ip})
                if cleaned:
                    return cleaned
    # Fallback: simple paragraph split
    return _fallback_naive(story_text, num_scenes)
