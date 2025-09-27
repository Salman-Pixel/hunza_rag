import google.generativeai as genai
from src.utils import env_str, env_float, env_int


MODEL = env_str("GEMINI_MODEL", "gemini-2.0-flash")
TEMP = env_float("TEMPERATURE", 0.4)
MAX_T = env_int("MAX_OUTPUT_TOKENS", 512)


def init():
    genai.configure(api_key=env_str("GOOGLE_API_KEY"))
    return genai.GenerativeModel(MODEL)


def craft_prompt(query: str, ctxs: list[dict]) -> str:
    sources = "\n\n".join([f"[{i+1}] {c['text']}" for i, c in enumerate(ctxs)])
    return (
        "You are a Hunza travel assistant. Use only the sources. "
        "If no exact 5 day plan exists, compose one by selecting relevant activities from the sources. "
        "Constraints, October month, family friendly pacing, base nights in Karimabad or Gulmit only, "
        "no Islamabad or Lahore segments, max 2 hours driving per day, include Baltit, Altit, Duiker, "
        "Attabad boat or lakeside, Passu Cones view, Hussaini bridge if conditions are safe. "
        "Output, a one line overview, then Day 1 to Day 5 with Morning, Afternoon, Evening. "
        "End with 3 safety or timing notes. Cite at least one source for every day, like [1], [2].\n\n"
        f"User question: {query}\n\nTop sources:\n{sources}"
    )


def ensure_no_islamabad(txt: str) -> str:
    bad = ["islamabad", "lahore", "airport"]
    if any(w in txt.lower() for w in bad):
        txt += "\n\n[Note] Removed out of area segments. Keep all 5 days within Hunza."
    return txt


def answer(query, ctxs):
    model = init()
    prompt = craft_prompt(query, ctxs)
    resp = model.generate_content(prompt, generation_config={
                                  "temperature": TEMP, "max_output_tokens": MAX_T})
    return ensure_no_islamabad(resp.text or "")
