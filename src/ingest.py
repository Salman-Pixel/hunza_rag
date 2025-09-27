import os
import pickle
import json
from pathlib import Path
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from src.utils import env_str


def sanitize_meta(meta: dict) -> dict:
    clean = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, (list, tuple, set)):
            vals = [str(x)
                    for x in v if x is not None and str(x).strip() != ""]
            if vals:
                clean[k] = ",".join(vals)   # flatten lists
        else:
            clean[k] = str(v)
    return clean


DATA = Path("data/curated/itineraries.jsonl")
CHROMA_DIR = env_str("CHROMA_DIR", ".chroma")
BM25_FILE = env_str("BM25_INDEX", ".bm25.pkl")
EMB_MODEL = env_str("EMBED_MODEL", "intfloat/e5-small-v2")


def load_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def make_chunks(rec):
    base = {k: rec.get(k) for k in [
        "id", "title", "region", "season", "days", "source_file"]}
    base = sanitize_meta(base)

    chunks = []
    # itinerary
    chunks.append((
        f"{rec['id']}-itinerary",
        f"[Itinerary] {rec['title']} in {rec.get('region','')}. Days {rec.get('days')}.",
        base
    ))
    # day level
    for d in rec.get("day_plan", []):
        txt = f"[Day {d['day']}] {d.get('summary','')}"
        meta = sanitize_meta(base | {"day": d["day"], "occ": d.get("occ", 1)})
        cid = f"{rec['id']}-d{d['day']}-{d.get('occ', 1)}"
        chunks.append((cid, txt, meta))
    return chunks


def build_vector(chunks):
    # lazy import, so missing torch/numpy does not kill ingestion
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError(f"Sentence-Transformers unavailable: {e}")
    client = chromadb.PersistentClient(
        path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    coll = client.get_or_create_collection("itineraries")
    model = SentenceTransformer(EMB_MODEL)
    ids, docs, metas = zip(*chunks)
    embeds = model.encode(
        [f"passage: {d}" for d in docs], normalize_embeddings=True).tolist()
    coll.upsert(ids=list(ids), documents=list(docs),
                metadatas=list(metas), embeddings=embeds)


def build_bm25(chunks):
    texts = [c[1] for c in chunks]
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)
    with open(BM25_FILE, "wb") as f:
        pickle.dump({"bm25": bm25, "texts": texts, "chunks": chunks}, f)


def main():
    all_chunks = []
    for rec in load_jsonl(DATA):
        all_chunks.extend(make_chunks(rec))
    print(f"Prepared {len(all_chunks)} chunks")
    build_bm25(all_chunks)
    print("BM25 built at", BM25_FILE)
    try:
        build_vector(all_chunks)
        print("Vector index built in", CHROMA_DIR)
    except Exception as e:
        print(f"Vector index failed: {e}\nProceeding with BM25 only.")


if __name__ == "__main__":
    main()
