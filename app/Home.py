# app/Home.py
import streamlit as st
from ui_shared import inject_css, init_state, top_nav

inject_css()
ss = init_state()

st.title("📚 Children’s Storybook Generator")
top_nav("Home")

st.markdown("""
Welcome! This demo lets you **create** a short children's story with AI, **illustrate** key scenes,
and **read** it like a picture book. You can also **download** the story as a PDF.

- Start on **Create** to type or record your idea.
- Then go to **Read** to flip through your illustrated pages.
""")

c1, c2 = st.columns(2)
with c1:
    st.subheader("✏️ Create a Story")
    st.write("Write or speak a 1–2 sentence idea. The app will generate a story, illustrations, and build a PDF.")
    st.page_link("pages/1_Create_Story.py", label="Go to Create →")

with c2:
    st.subheader("📖 Read Your Story")
    st.write("Flip through pages with images and captions. Download your book when you're happy with it.")
    st.page_link("pages/2_Read_Story.py", label="Go to Read →")

if ss.story:
    st.markdown("---")
    st.subheader("Last story")
    st.write(f"**{ss.title}**")
    st.write(ss.story[:220] + ("..." if len(ss.story) > 220 else ""))
