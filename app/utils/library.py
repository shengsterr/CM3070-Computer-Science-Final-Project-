# app/utils/library.py
from __future__ import annotations
import json, shutil, time
from pathlib import Path
from typing import List, Dict, Optional

LIB_DIR = Path("data/library")

def _ensure():
    LIB_DIR.mkdir(parents=True, exist_ok=True)

def _now_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")

def save_snapshot(ss) -> str:
    """
    Save the current session_state story, images, scenes, and PDFs
    into a library entry. Returns the entry id (timestamp).
    """
    _ensure()
    if not ss.get("story"):
        raise ValueError("No story to save.")

    eid = _now_id()
    folder = LIB_DIR / eid
    folder.mkdir(parents=True, exist_ok=True)

    # text
    (folder / "story.txt").write_text(ss.story, encoding="utf-8")
    (folder / "title.txt").write_text(ss.title or "My Storybook", encoding="utf-8")

    # cover image
    cover_rel = None
    if ss.get("image_path") and Path(ss.image_path).exists():
        cover_dest = folder / "cover.png"
        shutil.copy(ss.image_path, cover_dest)
        cover_rel = "cover.png"

    # scenes (captions + images)
    scenes_meta: List[Dict] = []
    if ss.get("scenes"):
        scenes_dir = folder / "scenes"
        scenes_dir.mkdir(exist_ok=True)
        for i, sc in enumerate(ss.scenes, 1):
            img_rel = None
            ipath = sc.get("image_path")
            if ipath and Path(ipath).exists():
                dest = scenes_dir / f"scene_{i:02d}.png"
                shutil.copy(ipath, dest)
                img_rel = f"scenes/scene_{i:02d}.png"
            scenes_meta.append({"caption": sc.get("caption", ""), "image_path": img_rel})

    # PDFs: always build a FRESH story-only PDF for this entry
    from pipelines.pdf import build_pdf

    story_pdf_name = "story.pdf"
    cover_abs = (folder / "cover.png") if cover_rel else None
    images_for_story = [cover_abs.as_posix()] if cover_abs and cover_abs.exists() else []
    build_pdf(ss.title, ss.story, images_for_story, str(folder / story_pdf_name))
    last_story_pdf = story_pdf_name

    # If a scene-book exists in session, copy it too (optional)
    last_scene_pdf = ss.get("last_scene_pdf")
    if last_scene_pdf and Path(last_scene_pdf).exists():
        pdf_name = Path(last_scene_pdf).name
        shutil.copy(last_scene_pdf, folder / pdf_name)
        last_scene_pdf = pdf_name
    else:
        last_scene_pdf = None


    meta = {
        "id": eid,
        "title": ss.title or "My Storybook",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cover_image": cover_rel,
        "last_story_pdf": last_story_pdf,
        "last_scene_pdf": last_scene_pdf,
        "scenes": scenes_meta,
    }
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return eid

def list_entries(limit: int = 24) -> List[Dict]:
    """Return most recent entries (desc)."""
    _ensure()
    entries: List[Dict] = []
    for child in sorted(LIB_DIR.iterdir(), reverse=True):
        meta = child / "meta.json"
        if meta.exists():
            data = json.loads(meta.read_text(encoding="utf-8"))
            data["_folder"] = str(child)
            entries.append(data)
    return entries[:limit]

def load_entry_to_session(eid: str, ss) -> Dict:
    """Load a saved entry into session_state for reading."""
    folder = LIB_DIR / eid
    meta_path = folder / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Library entry {eid} not found.")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    # story & title
    story_path = folder / "story.txt"
    title_path = folder / "title.txt"
    ss.story = story_path.read_text(encoding="utf-8") if story_path.exists() else ""
    ss.title = title_path.read_text(encoding="utf-8") if title_path.exists() else "My Storybook"

    # cover
    cover_rel = meta.get("cover_image")
    ss.image_path = str((folder / cover_rel).as_posix()) if cover_rel else None

    # PDFs
    lsp = meta.get("last_story_pdf")
    lcp = meta.get("last_scene_pdf")
    ss.last_story_pdf = str((folder / lsp).as_posix()) if lsp else None
    ss.last_scene_pdf = str((folder / lcp).as_posix()) if lcp else None

    # scenes (absolute paths)
    scenes_abs = []
    for sc in meta.get("scenes", []):
        ip_rel = sc.get("image_path")
        ip_abs = str((folder / ip_rel).as_posix()) if ip_rel else None
        scenes_abs.append({"caption": sc.get("caption", ""), "image_path": ip_abs})
    ss.scenes = scenes_abs
    ss.page_idx = 0
    return meta
