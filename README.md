# Hunza Trip Planner (Local RAG)

FastAPI + Gemini Flash generator with BM25/Chroma retrieval over local itinerary PDFs.

## Run
```bash
conda activate rag_hunza
pip install -r requirements.txt
export GOOGLE_API_KEY=...   # or put it in .env
python -m src.ingest        # builds BM25; vectors optional
uvicorn src.server:app --reload --port 8000


## Structure
    *src/extract_text.py → PDF → TXT
    *src/parse_days.py → TXT → JSONL (days)
    src/ingest.py → JSONL → BM25 + Chroma
    *src/retriever.py / src/generator.py / src/chat.py
    *web/index.html → frontend (no build)