import sys
from rich.console import Console
from src.retriever import search_hybrid
from src.generator import answer


HUNZA_HINT = " in Hunza, Karimabad, Gulmit, Passu, Attabad, Duiker"


def ask(query: str):
    q = query
    low = query.lower()
    if not any(k in low for k in ["hunza", "karimabad", "gulmit", "passu", "attabad", "duiker", "altit", "baltit"]):
        q = query + HUNZA_HINT
    ctxs = search_hybrid(q)
    txt = answer(query, ctxs)
    return txt, ctxs


if __name__ == "__main__":
    q = " ".join(
        sys.argv[1:]) or "Plan a 3 day family trip in May based in Karimabad"
    txt, ctxs = ask(q)
    c = Console()
    c.rule("Answer")
    c.print(txt)
    c.rule("Citations")
    for i, cxt in enumerate(ctxs, 1):
        c.print(f"[{i}] {cxt['id']} | {cxt['meta']} | {cxt['text'][:110]}...")
