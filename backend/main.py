import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from llm_router import mcr_router
from pirs_rag import pirs_rag
from mfiles_rag import mf_rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

app = FastAPI(title="M-Files AI Legal Assistant Backend", version="1.0.0")

# Dovolimo CORS za komunikacijo z M-Files vmesnikom
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    model: str = "claude" # claude, gemini, mistral
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
    """
    Osrednja točka (MCR) - sprejme zahtevo iz M-Files in preusmeri na LLM
    skupaj s kontekstom iz PIRS in MF (RAG).
    """
    logger.info(f"Prejeta zahteva: model={request.model}, rag={request.use_rag}, query='{request.query}'")
    sources = []
    context = []
    
    if request.use_rag:
        try:
            # PIRS (Zunanja strokovna baza)
            pirs_results = pirs_rag.retrieve(request.query)
            for doc in pirs_results:
                sources.append(f"PIRS: {doc['source']} ({doc['section']})")
                context.append(f"[PIRS] {doc['source']} - {doc['section']}: {doc['content']}")
                
            # M-Files (Interna baza dokumentov)
            mf_results = mf_rag.retrieve(request.query)
            for doc in mf_results:
                sources.append(f"MF: {doc['filename']}")
                context.append(f"[M-Files] {doc['filename']}: {doc['content']}")
        except Exception as e:
            logger.error(f"Napaka pri pridobivanju RAG virov: {e}")
            raise HTTPException(status_code=500, detail="Napaka pri priklicu RAG virov.")

    # Uporabi MCR za preusmeritev na izbrani LLM s kontekstom
    try:
        reply = mcr_router.generate_response(request.query, request.model, context)
        logger.info("Odgovor uspessno generiran.")
    except Exception as e:
        logger.error(f"Napaka pri generiranju odgovora: {e}")
        raise HTTPException(status_code=500, detail="Napaka pri LLM generiranju.")
    
    return ChatResponse(
        reply=reply,
        model_used=request.model,
        sources=sources
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
