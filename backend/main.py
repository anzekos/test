import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from llm_router import mcr_router
from pirs_rag import pirs_rag
from mfiles_rag import mf_rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="M-Files AI Legal Assistant Backend", version="1.0.0")

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    model: str = "claude"
    use_rag: bool = True


class ChatResponse(BaseModel):
    reply: str
    model_used: str
    sources: List[str]


@app.get("/")
def read_root():
    return {"status": "M-Files AI Assistant Backend is running.", "mcr": "Online", "rag": "Online"}


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    logger.info(f"Prejeta zahteva: model={request.model}, rag={request.use_rag}, query='{request.query[:80]}'")
    sources: List[str] = []
    context: List[str] = []

    if request.use_rag:
        try:
            for doc in pirs_rag.retrieve(request.query):
                sources.append(f"PIRS: {doc['source']} ({doc['section']})")
                context.append(f"[PIRS] {doc['source']} - {doc['section']}: {doc['content']}")

            for doc in mf_rag.retrieve(request.query):
                sources.append(f"MF: {doc['filename']}")
                context.append(f"[M-Files] {doc['filename']}: {doc['content']}")
        except Exception as e:
            logger.error(f"Napaka pri RAG pridobivanju: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Napaka pri priklicu RAG virov.")

    try:
        # FIX: pravilno ime metode je route_llm_call (ne generate_response)
        reply = mcr_router.route_llm_call(request.model, request.query, context)
        logger.info("Odgovor uspešno generiran.")
    except Exception as e:
        logger.error(f"Napaka pri generiranju odgovora: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Napaka pri LLM generiranju.")

    return ChatResponse(reply=reply, model_used=request.model, sources=sources)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)