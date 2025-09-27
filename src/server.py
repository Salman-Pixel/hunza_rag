from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.retriever import search_hybrid
from src.generator import answer

app = FastAPI(title="Hunza RAG")

# If you decide to open the UI from another port, this keeps things easy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str


@app.post("/api/chat")
def chat(body: ChatIn):
    ctxs = search_hybrid(body.message)
    txt = answer(body.message, ctxs)
    # trim text to keep payload small
    cites = [{"id": c["id"], "text": c["text"], "meta": c["meta"]}
             for c in ctxs]
    return {"answer": txt, "citations": cites}


# Serve frontend from ./web folder (we'll put index.html there)
app.mount("/", StaticFiles(directory="web", html=True), name="web")
