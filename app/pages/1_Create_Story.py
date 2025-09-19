# app/pages/1_Create_Story.py
import os
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

from ui_shared import inject_css, init_state, split_paragraphs, top_nav

# Pipelines
from pipelines.stt import transcribe_audio
from pipelines.sentiment import detect_sentiment
from pipelines.story_gen import generate_story
from pipelines.image_gen import generate_image                  # local (SD/SDXL)
from pipelines.cloud_image import generate_image_cloud          # cloud (Stability)
from pipelines.tts import tts_to_file
from pipelines.pdf import build_pdf, build_pdf_from_scenes
from pipelines.scene_plan import plan_scenes
from utils.prompt_templates import story_user_prompt, image_prompt_from_scene
from utils.library import save_snapshot


# ------------------------------------------------------------------
load_dotenv()
inject_css()
ss = init_state()
top_nav("Create")

st.title("✏️ Create a Story")

# =================== Sidebar (advanced) ===================
with st.sidebar.expander("Advanced settings", expanded=False):
    DEFAULT_GGUF = "models/llms/llama-3.1-8b-instruct.Q4_K_M.gguf"
    MODEL_HINT = st.text_input("Local GGUF path (fallback)", DEFAULT_GGUF)

    USE_CLOUD_LLM = st.checkbox("Use Cloud LLM (Gemini)", value=True)
    USE_CLOUD_IMG = st.checkbox("Use Cloud Images (Stability)", value=True)

    IMG_MODEL = st.selectbox(
        "Image model (local fallback)",
        ["auto", "stabilityai/sd-turbo", "stabilityai/sdxl-turbo"],
        help="Used only if cloud image gen is off or fails.",
    )
    STEPS = st.slider("Image steps", 4, 30, 6, step=1)

    STT_MODEL = st.selectbox("STT model (Whisper)", ["tiny", "base", "small", "medium", "large-v3"], index=2)
    STT_PREC  = st.selectbox("STT precision", ["int8", "int8_float16", "float16", "float32"], index=0)

    NUM_SCENES = st.slider("Number of scenes", 4, 8, 6)

# =================== Input Tabs ===================
tab1, tab2, tab3 = st.tabs(["✍️ Type a prompt", "📁 Upload audio", "🎙️ Record audio"])
with tab1:
    text_seed = st.text_area(
        "Your idea (1–2 sentences)",
        placeholder="A kid who finds a glowing seed and plants it under the moon..."
    )

with tab2:
    uploaded_audio = st.file_uploader("Upload a WAV/MP3/M4A", type=["wav", "mp3", "m4a"])

with tab3:
    st.caption("Click the mic to start/stop recording. Audio is processed locally for STT.")
    rec_bytes = audio_recorder(text="", pause_threshold=1.0, sample_rate=16000, icon_size="4x")
    if rec_bytes:
        st.audio(rec_bytes, format="audio/wav")
        st.session_state["rec_bytes"] = rec_bytes
    if st.button("🧹 Clear recording"):
        st.session_state.pop("rec_bytes", None)
        st.success("Recording cleared.")

# =================== Action Row ===================
col1, col2, col3, col4 = st.columns(4)
with col1:
    go = st.button("✨ Generate Story", type="primary")
with col2:
    img_go = st.button("🖼️ Generate Illustration")
with col3:
    pdf_go = st.button("📄 Build PDF")
with col4:
    book_go = st.button("📘 Produce Book")

# =================== Generate Story ===================
if go:
    seed_text = ""
    if ss.get("rec_bytes"):
        tmp = Path("data/tmp_recorded.wav"); tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(ss["rec_bytes"])
        seed_text = transcribe_audio(str(tmp), model_size=STT_MODEL, compute_type=STT_PREC, device="cpu")
    elif uploaded_audio is not None:
        ext = Path(uploaded_audio.name).suffix or ".wav"
        tmp = Path(f"data/tmp_uploaded{ext}"); tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(uploaded_audio.read())
        seed_text = transcribe_audio(str(tmp), model_size=STT_MODEL, compute_type=STT_PREC, device="cpu")
    else:
        seed_text = (text_seed or "").strip()

    if not seed_text:
        st.warning("Please type a prompt, upload audio, or record audio.")
    else:
        sentiment = detect_sentiment(seed_text)
        user_prompt = story_user_prompt(seed_text, sentiment)
        story = generate_story(user_prompt, gguf_path=MODEL_HINT if MODEL_HINT else None, prefer_cloud=USE_CLOUD_LLM)
        ss.story = story
        ss.title = "Story about " + (seed_text[:40] + ("..." if len(seed_text) > 40 else ""))
        ss.scenes = []
        ss.page_idx = 0
        st.success(f"Story generated (sentiment: {sentiment}).")

# =================== Show / Edit Story ===================
if ss.story:
    st.markdown('<span class="pill">STORY</span>', unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="story-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="story-title">{ss.title}</div>', unsafe_allow_html=True)

        if st.toggle("Edit text", value=False):
            ss.story = st.text_area("Edit story", ss.story, height=320)
        else:
            for para in split_paragraphs(ss.story):
                st.markdown(f'<div class="story-paragraph">{para}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if st.button("🔊 Read Aloud (save WAV)"):
            out_audio = Path("data/audio/story.wav"); out_audio.parent.mkdir(parents=True, exist_ok=True)
            tts_to_file(ss.story, str(out_audio)); st.audio(str(out_audio))
            st.success(f"Saved narration → {out_audio}")

        if ss.image_path and Path(ss.image_path).exists():
            st.image(ss.image_path, caption="Illustration", use_container_width=True)

# =================== Single Illustration ===================
if img_go:
    if not ss.story:
        st.warning("Please generate a story first.")
    else:
        main_scene = ss.story.split("\n\n")[0]
        base = image_prompt_from_scene(main_scene)
        img_prompt = f"No text on the image. {base}"
        out_img = Path("data/images/scene.png"); out_img.parent.mkdir(parents=True, exist_ok=True)

        img_path = None
        if USE_CLOUD_IMG:
            img_path = generate_image_cloud(img_prompt, str(out_img), steps=STEPS or 12)
        if not img_path:
            chosen = None if IMG_MODEL == "auto" else IMG_MODEL
            img_path = generate_image(img_prompt, str(out_img), model_id=chosen, steps=STEPS)

        ss.image_path = img_path
        st.success(f"Image generated → {img_path}")

if ss.image_path and Path(ss.image_path).exists():
    st.subheader("🎨 Illustration")
    st.image(ss.image_path, use_container_width=True)

# =================== Save snapshot ===================
if ss.story:
    if st.button("💾 Save to Library", help="Save this story, images, scenes and PDFs to your Library"):
        eid = save_snapshot(ss)
        st.success(f"Saved to Library! (ID: {eid})")
        st.info("Open the Library page to view it.")


# =================== Simple Story PDF ===================
if pdf_go:
    if not ss.story:
        st.warning("Generate a story first.")
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        images = [ss.image_path] if ss.image_path else []
        out_pdf = Path(f"data/pdfs/storybook_{ts}.pdf"); out_pdf.parent.mkdir(parents=True, exist_ok=True)
        build_pdf(ss.title, ss.story, images, str(out_pdf))
        ss.last_story_pdf = str(out_pdf)  # remember latest
        st.success(f"PDF saved → {out_pdf}")
        with open(out_pdf, "rb") as f:
            st.download_button("⬇️ Download PDF", data=f, file_name=out_pdf.name, mime="application/pdf")

# =================== Full Scene Book ===================
if book_go:
    if not ss.story:
        st.warning("Generate a story first.")
    else:
        with st.status("Planning scenes…", expanded=True):
            ss.scenes = plan_scenes(ss.story, num_scenes=NUM_SCENES, prefer_cloud=True)
            ss.page_idx = 0
            st.write(f"Planned {len(ss.scenes)} scenes.")

        prog = st.progress(0, text="Generating images…")
        for i, sc in enumerate(ss.scenes, 1):
            base = sc.get("image_prompt") or image_prompt_from_scene(sc["caption"])
            img_prompt = f"No text on the image. {base}"
            out_img = Path(f"data/images/scene_{i:02d}.png"); out_img.parent.mkdir(parents=True, exist_ok=True)

            img_path = None
            if USE_CLOUD_IMG:
                img_path = generate_image_cloud(img_prompt, str(out_img), steps=STEPS or 12)
            if not img_path:
                chosen = None if IMG_MODEL == "auto" else IMG_MODEL
                img_path = generate_image(img_prompt, str(out_img), model_id=chosen, steps=STEPS)

            sc["image_path"] = img_path
            prog.progress(i / max(1, len(ss.scenes)))
        prog.empty()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_pdf = Path(f"data/pdfs/storybook_scenes_{ts}.pdf")
        build_pdf_from_scenes(ss.title, ss.scenes, str(out_pdf))
        ss.last_scene_pdf = str(out_pdf)  # remember latest
        st.success(f"PDF saved → {out_pdf}")
        with open(out_pdf, "rb") as f:
            st.download_button("⬇️ Download Scene Book", data=f, file_name=out_pdf.name, mime="application/pdf")
