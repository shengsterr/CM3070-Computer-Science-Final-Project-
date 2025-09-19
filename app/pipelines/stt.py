import os
from faster_whisper import WhisperModel

def transcribe_audio(
    audio_path: str,
    model_size: str = "small",          # tiny, base, small, medium, large-v3
    compute_type: str = "int8",         # int8 on CPU is fast & accurate enough
    device: str = "cpu",                # <-- force CPU (no cuDNN needed)
):
    # Force CTranslate2 to stay on CPU even if a GPU is present/misconfigured.
    if device.lower() == "cpu":
        os.environ["CT2_FORCE_CPU"] = "1"
    else:
        os.environ.pop("CT2_FORCE_CPU", None)

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(
        audio_path,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        beam_size=5,
    )
    return " ".join(s.text.strip() for s in segments).strip()
