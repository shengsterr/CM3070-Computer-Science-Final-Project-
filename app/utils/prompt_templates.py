STORY_SYSTEM = """You are a friendly children's book author.
Write in simple, vivid language for ages 6–9. Keep it wholesome, kind, and imaginative.
Target length: 6–9 short paragraphs (2–3 sentences each).
End with a gentle lesson in one sentence."""

SCENE_STYLE = "children's picture book, soft watercolor, bright, friendly, whimsical, simple shapes, high contrast, clean composition"

def story_user_prompt(user_seed: str, sentiment: str) -> str:
    tone = {
        "POSITIVE": "joyful and adventurous",
        "NEGATIVE": "comforting and hopeful (but not sad)",
        "NEUTRAL":  "curious and calm"
    }.get(sentiment.upper(), "curious and calm")
    return (
        f"Seed idea: {user_seed}\n"
        f"Desired tone: {tone}\n"
        "Include a clear beginning, middle, and end. "
        "Use a consistent main character and setting. "
        "Avoid brand names, violence, or scary imagery."
    )

def image_prompt_from_scene(scene_text: str, character_hint: str = "a brave child and a friendly creature") -> str:
    return (
        f"{SCENE_STYLE}. Illustration of {character_hint}. Depict: {scene_text}. "
        "No text on image. Child-friendly, cozy, storybook aesthetic."
    )
