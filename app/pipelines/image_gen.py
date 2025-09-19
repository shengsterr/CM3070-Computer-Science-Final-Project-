from pathlib import Path
import torch
from PIL import Image

def generate_image(prompt: str, out_path: str, model_id: str | None = None, steps: int = 6):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from diffusers import AutoPipelineForText2Image
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if model_id is None:
            # Lighter model on CPU; SDXL-Turbo on GPU
            model_id = "stabilityai/sdxl-turbo" if device == "cuda" else "stabilityai/sd-turbo"
        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id, torch_dtype=torch.float16 if device == "cuda" else torch.float32
        ).to(device)
        image = pipe(prompt, num_inference_steps=steps, guidance_scale=0.0).images[0]
        image.save(out_path)
        return str(out_path)
    except Exception:
        Image.new("RGB", (1024, 768), (240, 250, 255)).save(out_path)
        return str(out_path)
