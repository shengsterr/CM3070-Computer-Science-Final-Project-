from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

def paths_for_run():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = DATA_DIR / ts
    audio = base / "audio.wav"
    story = base / "story.txt"
    image = base / "image.png"
    pdf   = base / "storybook.pdf"
    base.mkdir(parents=True, exist_ok=True)
    return dict(base=base, audio=audio, story=story, image=image, pdf=pdf)
