import os
import sys
import pathlib
from pdfminer.high_level import extract_text as pdfminer_extract
from pypdf import PdfReader
from src.utils import ensure_dir, clean_text
from bs4 import BeautifulSoup


# RAW = pathlib.Path("data/raw_pdfs")
RAW = pathlib.Path("data/raw_pdfs/hunza_itineraries")
OUT = pathlib.Path("data/staging_txt")
ensure_dir(OUT.as_posix())


def extract_pdf(path: pathlib.Path) -> str:
    try:
        return pdfminer_extract(path.as_posix())
    except Exception:
        # fallback
        reader = PdfReader(path.as_posix())
        return "\n".join([p.extract_text() or "" for p in reader.pages])


def extract_html(path: pathlib.Path) -> str:
    html = path.read_text(encoding="utf-8", errors="ignore")
    # install beautifulsoup4 and lxml if missing
    soup = BeautifulSoup(html, "lxml")
    # remove scripts and styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text("\n")


def main():
    files = list(RAW.glob("**/*"))
    if not files:
        print("No files in data/raw_pdfs")
        return
    for f in files:
        if not f.is_file():
            continue
        out = OUT / (f.stem + ".txt")
        try:
            if f.suffix.lower() in {".pdf"}:
                txt = extract_pdf(f)
            elif f.suffix.lower() in {".htm", ".html"}:
                txt = extract_html(f)
            else:
                # treat unknown as text
                txt = f.read_text(encoding="utf-8", errors="ignore")
            out.write_text(clean_text(txt), encoding="utf-8")
            print(f"Wrote {out}")
        except Exception as e:
            print(f"Failed {f.name}: {e}")


if __name__ == "__main__":
    main()
