import os, requests
from pathlib import Path
from typing import Optional

V2_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

def generate_image_cloud(
    prompt: str,
    out_path: str,
    steps: int = 12,              # unused by v2beta, kept for UI
    width: int = 1024,            # unused by v2beta
    height: int = 1024,           # unused by v2beta
    aspect_ratio: str = "1:1",
) -> Optional[str]:
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        print("[cloud_image] No STABILITY_API_KEY set.")
        return None

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # NOTE: don't set Content-Type; requests will add the multipart boundary
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }
    files = {
        "prompt": (None, prompt),
        "aspect_ratio": (None, aspect_ratio),
        # Optional extras:
        # "negative_prompt": (None, "text, watermark, logo"),
        # "output_format": (None, "png"),
    }

    try:
        r = requests.post(V2_URL, headers=headers, files=files, timeout=180)
        if r.status_code == 200:
            out.write_bytes(r.content)     # raw PNG/JPEG bytes
            return str(out)
        print(f"[cloud_image] {r.status_code} {r.reason}: {r.text[:500]}")
        return None
    except Exception as e:
        print(f"[cloud_image] Error: {e}")
        return None
