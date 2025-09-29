# generator.py
from src.utils import env_str, env_float, env_int
import google.generativeai as genai

MODEL = env_str("GEMINI_MODEL", "gemini-2.0-flash")
TEMP = env_float("TEMPERATURE", 0.4)
MAX_T = env_int("MAX_OUTPUT_TOKENS", 512)


def init():
    genai.configure(api_key=env_str("GOOGLE_API_KEY"))
    return genai.GenerativeModel(MODEL)


def is_relevant(query: str, ctxs: list[dict]) -> bool:
    """
    Returns True if query has context or travel-related keywords.
    """
    hunza_keywords = [
        "hunza", "gilgit", "karimabad", "gulmit", "altit", "baltit",
        "attabad", "passu", "duiker", "hussaini", "eagle nest"
    ]
    q = query.lower()
    if any(k in q for k in hunza_keywords):
        return True
    if ctxs:  # if retriever found context snippets, treat as relevant
        return True
    return False


def craft_prompt(query: str, ctxs: list[dict]) -> str:
    sources = "\n\n".join([f"[{i+1}] {c['text']}" for i, c in enumerate(ctxs)])
    return (
        "You are a helpful Hunza travel assistant. "
        "Answer the user's question using the sources below. "
        "If the answer is not in the sources, say you don’t know.\n\n"
        f"User question: {query}\n\nTop sources:\n{sources}"
    )


def answer(query, ctxs):
    if not is_relevant(query, ctxs):
        return "I can only answer questions related to Hunza travel."

    model = init()
    prompt = craft_prompt(query, ctxs)
    resp = model.generate_content(prompt, generation_config={
        "temperature": TEMP,
        "max_output_tokens": MAX_T
    })
    return resp.text or ""
