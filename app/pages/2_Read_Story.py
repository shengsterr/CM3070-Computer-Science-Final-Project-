# app/pages/2_Read_Story.py
from pathlib import Path

import streamlit as st
from ui_shared import inject_css, init_state, split_paragraphs, top_nav, READ_MODE_IMG_WIDTH

inject_css()
ss = init_state()
top_nav("Read")

st.title("📖 Read Your Story")

# =================== Story (text) ===================
if not ss.story:
    st.info("No story yet. Go to **Create** to make one.")
else:
    st.markdown('<span class="pill">STORY</span>', unsafe_allow_html=True)
    st.markdown('<div class="story-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="story-title">{ss.title}</div>', unsafe_allow_html=True)
    for para in split_paragraphs(ss.story):
        st.markdown(f'<div class="story-paragraph">{para}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =================== Storybook Preview ===================
if ss.get("scenes"):
    st.markdown("---")
    st.subheader("Picture Book")

    n = len(ss.scenes)
    sc = ss.scenes[ss.page_idx]

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="page-card">', unsafe_allow_html=True)
        if sc.get("image_path") and Path(sc["image_path"]).exists():
            st.image(sc["image_path"], width=READ_MODE_IMG_WIDTH)
        else:
            st.info("Image not available for this page.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="page-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="caption-box"><div class="caption">{sc.get("caption","")}</div></div>',
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Nav buttons (below content) ----
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
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Downloads (latest) ----
    col1, col2 = st.columns(2)
    with col1:
        last_scene = ss.get("last_scene_pdf")
        if last_scene and Path(last_scene).exists():
            with open(last_scene, "rb") as f:
                st.download_button("⬇️ Download Scene Book", data=f,
                                file_name=Path(last_scene).name, mime="application/pdf",
                                key=f"dl_scene_read_{Path(last_scene).name}")

    with col2:
        # Always rebuild the Story PDF from the CURRENT story before offering download
        from pipelines.pdf import build_pdf
        tmp_latest = Path("data/pdfs/storybook_latest.pdf")
        imgs = [ss.image_path] if ss.image_path and Path(ss.image_path).exists() else []
        build_pdf(ss.title, ss.story, imgs, str(tmp_latest))
        with open(tmp_latest, "rb") as f:
            st.download_button("⬇️ Download Story PDF", data=f,
                            file_name="storybook.pdf", mime="application/pdf",
                            key="dl_story_read_latest")
