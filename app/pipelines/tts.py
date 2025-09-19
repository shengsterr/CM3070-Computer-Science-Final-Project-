from pathlib import Path
import pyttsx3

def tts_to_file(text: str, out_wav: str):
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.save_to_file(text, str(out))
    engine.runAndWait()
    return str(out)
