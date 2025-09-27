import pathlib
import json
import re
from src.utils import clean_text


STAGING = pathlib.Path("data/staging_txt")
CURATED = pathlib.Path("data/curated/itineraries.jsonl")

# --- at top ---
DAY_RE = re.compile(r'(?im)^\s*day[\s:-]*(\d{1,2})\b.*$')


def split_days(text: str):
    hits = list(DAY_RE.finditer(text))
    if not hits:
        return []
    blocks = []
    for i, m in enumerate(hits):
        start = m.start()
        end = hits[i+1].start() if i+1 < len(hits) else len(text)
        block = text[start:end].strip()
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        # first non empty line after header acts as summary seed
        summary = " ".join(lines[1:6])[:800] if len(lines) > 1 else ""
        blocks.append({"day": int(m.group(1)), "summary": summary})

    # assign occurrence index per repeated day number
    counts = {}
    out = []
    for b in blocks:
        d = b["day"]
        counts[d] = counts.get(d, 0) + 1
        b["occ"] = counts[d]
        if b["summary"]:
            out.append(b)
    # sort by day then occurrence
    out.sort(key=lambda x: (x["day"], x["occ"]))
    return out


def infer_title(text: str, fallback: str):
    # grab first non empty line as title
    for ln in text.splitlines():
        ln = ln.strip()
        if ln:
            return ln[:120]
    return fallback


def main():
    CURATED.unlink(missing_ok=True)
    out = CURATED.open("a", encoding="utf-8")
    for txtfile in STAGING.glob("*.txt"):
        raw = txtfile.read_text(encoding="utf-8", errors="ignore")
        raw = clean_text(raw)
        days = split_days(raw)
        if not days:
            print(f"Skip, no Day headings found in {txtfile.name}")
            continue
        rec = {
            "id": txtfile.stem.lower().replace(" ", "-"),
            "title": infer_title(raw, txtfile.stem),
            "region": "GB",
            "season": [],
            "days": len(days),
            "difficulty": None,
            "transport": [],
            "source_file": txtfile.stem,
            "day_plan": days
        }
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"Added {txtfile.name} with {len(days)} days")
    out.close()
    print(f"Wrote {CURATED}")


if __name__ == "__main__":
    main()
