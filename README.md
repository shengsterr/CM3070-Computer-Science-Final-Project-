# AI Children’s Story Generator 📚✨

Turn a one-sentence idea into a printable, illustrated, narrated **children’s picture book**—in minutes.

Built with **Streamlit** and an orchestration of ASR (speech-to-text), LLM story generation, scene planning, text-to-image, TTS narration, and PDF export. Cloud models are used for quality and speed with local fallbacks for resilience.

---

## Table of contents
- [Features](#features)
- [Quick start](#quick-start)

---

## Features

- **Create** from text or voice (Whisper-style STT)  
- **Story generation** (Gemini 1.5 Flash by default; local LLM fallback)  
- **Scene planning** into page-level captions for better image alignment  
- **Illustrations** via Stability **Stable Image Core** (cloud) or local Diffusers fallback  
- **Narration (TTS)** to a WAV file (optional)  
- **Exports**: Picture-book PDF and Story-only PDF  
- **Library**: save, re-open, re-generate pages  
- **Guardrails**: sentiment→tone mapping, safe prompt templates, “no text in image,” basic output checks  
- **Offline-capable path** (reduced quality) when cloud is unavailable

---

## Quick start

### 1) Clone and set up
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# (Recommended) create a venv
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
### 2) Run the application
```
cd "path\to\folder"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m streamlit run app/Home.py
```
