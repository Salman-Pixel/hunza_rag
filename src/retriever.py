import os
import pickle
from src.utils import env_str, env_int

CHROMA_DIR = env_str("CHROMA_DIR", ".chroma")
BM25_FILE = env_str("BM25_INDEX", ".bm25.pkl")
EMB_MODEL = env_str("EMBED_MODEL", "intfloat/e5-small-v2")
K_VEC = env_int("VECTOR_TOP_K", 12)
K_BM25 = env_int("BM25_TOP_K", 30)
K_FINAL = env_int("FINAL_K", 4)


# add near the top, below imports and env reads
HUNZA_KEYS = [
    "hunza", "karimabad", "altit", "baltit", "duiker", "eagle", "attabad",
    "gulmit", "passu", "hussaini", "borith", "khunjerab", "aliabad", "ganaish"
]
NEG_KEYS = ["islamabad", "lahore", "airport", "contingency", "wagah", "rohtas"]


def keyword_boost(text: str) -> float:
    t = text.lower()
    b = 0.0
    for k in HUNZA_KEYS:
        if k in t:
            b += 0.25
    for k in NEG_KEYS:
        if k in t:
            b -= 0.25
    return b


def is_hunzaish(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in HUNZA_KEYS)


# Load BM25 first, fail early with a helpful message if missing
if not os.path.exists(BM25_FILE):
    raise SystemExit("BM25 index not found. Run: python -m src.ingest")

with open(BM25_FILE, "rb") as f:
    pkg = pickle.load(f)
    bm25 = pkg["bm25"]
    texts = pkg["texts"]
    chunks = pkg["chunks"]

# Try to enable vector search, otherwise fall back to BM25 only
USE_VECTOR = True
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    coll = client.get_or_create_collection("itineraries")
    model = SentenceTransformer(EMB_MODEL)
except Exception as e:
    print(f"Vector search disabled: {e}")
    USE_VECTOR = False


def embed_query(q: str):
    if not USE_VECTOR:
        return None
    return model.encode([f"query: {q}"], normalize_embeddings=True).tolist()[0]


def search_hybrid(query: str):
    # vector hits
    v_hits = {}
    if USE_VECTOR:
        try:
            qemb = embed_query(query)
            v = coll.query(
                query_embeddings=[qemb],
                n_results=K_VEC,
                include=["documents", "metadatas", "distances"]  # remove "ids"

            )

            for i in range(len(v["ids"][0])):
                v_hits[v["ids"][0][i]] = {
                    "text": v["documents"][0][i],
                    "meta": v["metadatas"][0][i],
                    "sv": 1.0 - v["distances"][0][i],
                    "sb": 0.0
                }
        except Exception as e:
            print(f"Vector query failed: {e}")

    # bm25 hits
    toks = query.lower().split()
    scores = bm25.get_scores(toks)
    ranked = sorted(enumerate(scores),
                    key=lambda x: x[1], reverse=True)[:K_BM25]
    for idx, sc in ranked:
        cid, ctext, cmeta = chunks[idx]
        if cid in v_hits:
            v_hits[cid]["sb"] = float(sc)
        else:
            v_hits[cid] = {"text": ctext, "meta": cmeta,
                           "sv": 0.0, "sb": float(sc)}

    # blend
    for it in v_hits.values():
        it["score"] = 0.6 * it["sv"] + 0.4 * \
            max(0.0, it["sb"]) + keyword_boost(it["text"])

    # prefer hunza chunks, but if none, keep what we have
    items = list(v_hits.items())
    hunza_items = [kv for kv in items if is_hunzaish(kv[1]["text"])]
    ranked_pool = hunza_items if hunza_items else items

    final = sorted(ranked_pool, key=lambda kv: kv[1]["score"], reverse=True)[
        :K_FINAL]
    return [{"id": k, "text": v["text"], "meta": v["meta"], "score": v["score"]} for k, v in final]
