from transformers import pipeline

_classifier = pipeline("sentiment-analysis", model="distilroberta-base")

def detect_sentiment(text: str) -> str:
    if not text.strip():
        return "NEUTRAL"
    out = _classifier(text[:512])[0]["label"].upper()
    return out if out in {"POSITIVE", "NEGATIVE"} else "NEUTRAL"
