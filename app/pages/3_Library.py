# app/pages/3_Library.py
from pathlib import Path
import streamlit as st

from ui_shared import inject_css, init_state, top_nav
from utils.library import list_entries, load_entry_to_session

inject_css()
ss = init_state()
top_nav("Library")

st.title("🗂️ Library")

entries = list_entries(limit=30)
if not entries:
    st.info("No saved stories yet. Create one on the **Create** page, then click **Save to Library**.")
else:
    cols = st.columns(3)
    for i, e in enumerate(entries):
        with cols[i % 3]:
            st.markdown("----")
            # cover image or placeholder
            cover = e.get("cover_image")
            folder = Path(e["_folder"])
            if cover and (folder / cover).exists():
                st.image(str(folder / cover), use_container_width=True)
            else:
                st.write("*(No cover image)*")
            st.subheader(e.get("title", "Untitled"))
            st.caption(f"Created: {e.get('created_at','')} · ID: `{e.get('id','')}`")

            btn_read = st.button("📖 Read", key=f"read_{e['id']}")
            if btn_read:
                load_entry_to_session(e["id"], ss)
                st.switch_page("pages/2_Read_Story.py")

            # downloads if snapshots have PDFs
            last_scene_pdf = e.get("last_scene_pdf")
            last_story_pdf = e.get("last_story_pdf")
            if last_scene_pdf and (folder / last_scene_pdf).exists():
                with open(folder / last_scene_pdf, "rb") as f:
                    st.download_button("⬇️ Scene Book PDF", data=f, file_name=(folder / last_scene_pdf).name, mime="application/pdf", key=f"dl_scene_{e['id']}")
            if last_story_pdf and (folder / last_story_pdf).exists():
                with open(folder / last_story_pdf, "rb") as f:
                    st.download_button("⬇️ Story PDF", data=f, file_name=(folder / last_story_pdf).name, mime="application/pdf", key=f"dl_story_{e['id']}")
