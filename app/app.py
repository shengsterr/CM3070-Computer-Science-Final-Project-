import os
from pathlib import Path
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

# Load keys from .env (GEMINI_API_KEY, STABILITY_API_KEY)
load_dotenv()

# --- local & cloud pipelines ---
from pipelines.stt import transcribe_audio
from pipelines.sentiment import detect_sentiment
from pipelines.story_gen import generate_story
from pipelines.image_gen import generate_image                # local SD/SDXL fallback
from pipelines.cloud_image import generate_image_cloud        # cloud (Stability v2beta)
from pipelines.tts import tts_to_file
from pipelines.pdf import build_pdf, build_pdf_from_scenes
from pipelines.scene_plan import plan_scenes
from utils.prompt_templates import story_user_prompt, image_prompt_from_scene


# =================== SMALL UI HELPERS ===================
def inject_css(font_px: int = 22, line_h: float = 1.6):
    """Inject lightweight styling for comfy reading + cards."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
        :root {{
          --story-font-size: {font_px}px;
          --story-line-height: {line_h};
          --accent:#7c3aed; --fg:#f8fafc;
        }}
        html, body, [class*="css"] {{
          font-family: 'Nunito', system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important;
        }}

        .story-card {{
          background: #0f172a; color:#e5e7eb;
          border:1px solid #1f2937; border-radius: 18px; padding: 20px 22px;
          box-shadow: none; margin: 10px 0;
        }}
        .story-title {{
          font-weight: 800; font-size: calc(var(--story-font-size) + 8px);
          margin: 6px 0 12px 0;
        }}
        .story-paragraph {{
          font-size: var(--story-font-size);
          line-height: var(--story-line-height);
          margin: 8px 0;
        }}

        /* clean preview cards (no white bars) */
        .page-card {{ background: transparent; padding: 0; border-radius: 0; box-shadow: none; }}
        .stImage img {{ border-radius: 16px; display: block; }}

        .caption-box {{
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.09);
          border-radius: 14px;
          padding: 12px 14px;
        }}
        .caption {{
          font-size: {max(16, font_px-2)}px;
          line-height: 1.55;
          margin: 0;
        }}

        /* Buttons */
        .stButton>button {{
          background: linear-gradient(180deg, var(--accent), #6d28d9);
          border: 0; color: var(--fg); border-radius: 12px;
          padding: 10px 14px; font-weight: 700;
          box-shadow: 0 6px 18px rgba(124,58,237,0.25);
        }}
        .stButton>button:hover {{ filter: brightness(1.08); }}

        .nav-row .stButton>button {{
          background:#111827; border:1px solid #1f2937; color:#e5e7eb; box-shadow:none;
        }}
        .nav-row .stButton>button:hover {{ background:#0b1220; }}

        .pill {{
          display:inline-block; padding: 4px 10px; border-radius: 999px;
          background:#eef2ff; color:#3730a3; font-size:12px; font-weight:700;
          margin-right:8px;
        }}

        /* Hide any lingering progress bar fill */
        .stProgress > div > div {{ background:transparent !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in (text or "").split("\n\n") if p.strip()]


# =================== PAGE SETUP ===================
st.set_page_config(page_title="Children's Storybook Generator",
                   page_icon="📚", layout="wide")
st.title("📚 Children’s Storybook Generator")

# Basic reading controls always visible
READING_MODE = st.sidebar.checkbox("Reading mode (bigger text)", value=True)
FONT_PX = st.sidebar.slider("Reading size", 16, 36, 22)
inject_css(font_px=FONT_PX)

# Mode switch
MODE = st.sidebar.radio("Mode", ["Create", "Read"], horizontal=True)

# Advanced settings tucked away
with st.sidebar.expander("Advanced settings", expanded=False):
    DEFAULT_GGUF = "models/llms/llama-3.1-8b-instruct.Q4_K_M.gguf"  # optional local fallback
    MODEL_HINT = st.text_input("Local GGUF path (fallback)", DEFAULT_GGUF)

    USE_CLOUD_LLM = st.checkbox("Use Cloud LLM (Gemini)", value=True)
    USE_CLOUD_IMG = st.checkbox("Use Cloud Images (Stability)", value=True)

    IMG_MODEL = st.selectbox(
        "Image model (local fallback)",
        ["auto", "stabilityai/sd-turbo", "stabilityai/sdxl-turbo"],
        help="Used only if cloud image gen is off or fails.",
    )
    STEPS = st.slider("Image steps", 4, 30, 6, step=1)

    # Whisper (forced CPU for reliability)
    STT_MODEL = st.selectbox("STT model (Whisper)", ["tiny", "base", "small", "medium", "large-v3"], index=2)
    STT_PREC  = st.selectbox("STT precision", ["int8", "int8_float16", "float16", "float32"], index=0,
                              help="Use int8 on CPU; float16 on NVIDIA GPU if configured.")

    # Multi-scene book
    NUM_SCENES = st.slider("Number of scenes", 4, 8, 6)

# Fixed width for preview image in Read mode (smaller to fit)
READ_MODE_IMG_WIDTH = 800

# =================== SESSION DEFAULTS ===================
ss = st.session_state
ss.setdefault("story", "")
ss.setdefault("image_path", None)
ss.setdefault("title", "My Storybook")
ss.setdefault("scenes", [])     # planned scenes w/ image_path
ss.setdefault("page_idx", 0)    # current page index for preview

# =================== CREATE MODE ===================
if MODE == "Create":
    # ---------- Input tabs ----------
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

    # ---------- Action row ----------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        go = st.button("✨ Generate Story", type="primary")
    with col2:
        img_go = st.button("🖼️ Generate Illustration")
    with col3:
        pdf_go = st.button("📄 Build PDF")
    with col4:
        book_go = st.button("📘 Produce Book")

    # ---------- Story generation ----------
    if go:
        seed_text = ""
        if ss.get("rec_bytes"):
            tmp = Path("data/tmp_recorded.wav"); tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(ss["rec_bytes"])
            seed_text = transcribe_audio(str(tmp), model_size=STT_MODEL, compute_type=STT_PREC, device="cpu")
        elif uploaded_audio is not None:
            tmp = Path("data/tmp_uploaded"); tmp.parent.mkdir(parents=True, exist_ok=True)
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

    # ---------- Story: read & edit ----------
    if ss.story:
        st.markdown('<span class="pill">STORY</span>', unsafe_allow_html=True)
        colA, colB = st.columns([3, 2])

        with colA:
            st.markdown('<div class="story-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="story-title">{ss.title}</div>', unsafe_allow_html=True)

            if READING_MODE:
                for para in split_paragraphs(ss.story):
                    st.markdown(f'<div class="story-paragraph">{para}</div>', unsafe_allow_html=True)
            else:
                ss.story = st.text_area("Edit story", ss.story, height=320)

            st.markdown("</div>", unsafe_allow_html=True)

        with colB:
            if st.button("🔊 Read Aloud (save WAV)"):
                out_audio = Path("data/audio/story.wav"); out_audio.parent.mkdir(parents=True, exist_ok=True)
                tts_to_file(ss.story, str(out_audio)); st.audio(str(out_audio))
                st.success(f"Saved narration → {out_audio}")

            if ss.image_path and Path(ss.image_path).exists():
                st.image(ss.image_path, caption="Illustration", use_container_width=True)

    # ---------- Single image generation ----------
    if img_go:
        if not ss.story:
            st.warning("Please generate a story first.")
        else:
            main_scene = ss.story.split("\n\n")[0]
            base = image_prompt_from_scene(main_scene)
            img_prompt = f"No text on the image. {base}"
            out_img = Path("data/images/scene.png")

            img_path = None
            if USE_CLOUD_IMG:
                img_path = generate_image_cloud(img_prompt, str(out_img), steps=STEPS if STEPS else 12)
            if not img_path:
                chosen = None if IMG_MODEL == "auto" else IMG_MODEL
                img_path = generate_image(img_prompt, str(out_img), model_id=chosen, steps=STEPS)

            ss.image_path = img_path
            st.success(f"Image generated → {img_path}")

    if ss.image_path and Path(ss.image_path).exists():
        st.markdown("---")
        st.subheader("🎨 Illustration")
        st.image(ss.image_path, use_container_width=True)

    # ---------- Simple PDF ----------
    if pdf_go:
        if not ss.story:
            st.warning("Generate a story first.")
        else:
            images = [ss.image_path] if ss.image_path else []
            out_pdf = Path("data/pdfs/storybook.pdf"); out_pdf.parent.mkdir(parents=True, exist_ok=True)
            build_pdf(ss.title, ss.story, images, str(out_pdf))
            st.success(f"PDF saved → {out_pdf}")
            with open(out_pdf, "rb") as f:
                st.download_button("⬇️ Download PDF", data=f, file_name="storybook.pdf", mime="application/pdf")

    # ---------- Multi-scene book ----------
    if book_go:
        if not ss.story:
            st.warning("Generate a story first.")
        else:
            with st.status("Planning scenes…", expanded=True):
                ss.scenes = plan_scenes(ss.story, num_scenes=NUM_SCENES, prefer_cloud=USE_CLOUD_LLM)
                ss.page_idx = 0
                st.write(f"Planned {len(ss.scenes)} scenes.")

            prog = st.progress(0, text="Generating images…")
            for i, sc in enumerate(ss.scenes, 1):
                base = sc.get("image_prompt") or image_prompt_from_scene(sc["caption"])
                img_prompt = f"No text on the image. {base}"
                out_img = Path(f"data/images/scene_{i:02d}.png")

                img_path = None
                if USE_CLOUD_IMG:
                    img_path = generate_image_cloud(img_prompt, str(out_img), steps=STEPS if STEPS else 12)
                if not img_path:
                    chosen = None if IMG_MODEL == "auto" else IMG_MODEL
                    img_path = generate_image(img_prompt, str(out_img), model_id=chosen, steps=STEPS)
                sc["image_path"] = img_path
                prog.progress(i / max(1, len(ss.scenes)))
            prog.empty()

            out_pdf = Path("data/pdfs/storybook_scenes.pdf")
            build_pdf_from_scenes(ss.title, ss.scenes, str(out_pdf))
            st.success(f"PDF saved → {out_pdf}")
            with open(out_pdf, "rb") as f:
                st.download_button("⬇️ Download Scene Book", data=f, file_name="storybook_scenes.pdf", mime="application/pdf")


# =================== READ MODE ===================
if MODE == "Read":
    if not ss.story:
        st.info("No story yet. Switch to **Create** mode to make one.")
    else:
        # Reading block
        st.markdown('<span class="pill">STORY</span>', unsafe_allow_html=True)
        st.markdown('<div class="story-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="story-title">{ss.title}</div>', unsafe_allow_html=True)
        for para in split_paragraphs(ss.story):
            st.markdown(f'<div class="story-paragraph">{para}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =================== STORYBOOK PREVIEW (shown in BOTH modes) ===================
if ss.get("scenes"):
    st.markdown("---")
    st.subheader("📖 Storybook Preview")

    n = len(ss.scenes)
    sc = ss.scenes[ss.page_idx]

    # Layout: smaller image in Read mode
    if MODE == "Read":
        left, right = st.columns([1, 1])
    else:
        left, right = st.columns([1.3, 1])

    with left:
        st.markdown('<div class="page-card">', unsafe_allow_html=True)
        if sc.get("image_path") and Path(sc["image_path"]).exists():
            if MODE == "Read":
                st.image(sc["image_path"], width=READ_MODE_IMG_WIDTH)
            else:
                st.image(sc["image_path"], use_container_width=True)
        else:
            st.info("Image not available for this page.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="page-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="caption-box"><div class="caption">{sc.get("caption","")}</div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Nav buttons BELOW content
    st.markdown('<div class="nav-row">', unsafe_allow_html=True)
    nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 2, 1, 1])
    with nav1:
        if st.button("⏮️ First", use_container_width=True, disabled=ss.page_idx == 0, key="first_btn"):
            ss.page_idx = 0
    with nav2:
        if st.button("⬅️ Prev", use_container_width=True, disabled=ss.page_idx == 0, key="prev_btn"):
            ss.page_idx = max(0, ss.page_idx - 1)
    with nav3:
        st.markdown(
            f"<div style='text-align:center; font-weight:700; padding-top:8px'>Page {ss.page_idx+1} / {n}</div>",
            unsafe_allow_html=True,
        )
    with nav4:
        if st.button("Next ➡️", use_container_width=True, disabled=ss.page_idx >= n - 1, key="next_btn"):
            ss.page_idx = min(n - 1, ss.page_idx + 1)
    with nav5:
        if st.button("Last ⏭️", use_container_width=True, disabled=ss.page_idx >= n - 1, key="last_btn"):
            ss.page_idx = n - 1
    st.markdown('</div>', unsafe_allow_html=True)

    # Downloads
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        if Path("data/pdfs/storybook_scenes.pdf").exists():
            with open("data/pdfs/storybook_scenes.pdf", "rb") as f:
                st.download_button("⬇️ Download Scene Book", data=f, file_name="storybook_scenes.pdf", mime="application/pdf")
    with col_dl2:
        if Path("data/pdfs/storybook.pdf").exists():
            with open("data/pdfs/storybook.pdf", "rb") as f:
                st.download_button("⬇️ Download Story PDF", data=f, file_name="storybook.pdf", mime="application/pdf")
