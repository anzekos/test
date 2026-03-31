import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
from llm_router import mcr_router
from persistence_manager import persistence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="M-Files AI Assistant Backend", version="2.0.0")

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response modeli ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" ali "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    model: str = "claude"
    messages: Optional[List[ChatMessage]] = None
    persona_instruction: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    model_used: str


class SaveChatRequest(BaseModel):
    id: str
    title: str
    messages: List[Dict[str, Any]]
    colleagueId: Optional[str] = None
    date: Optional[str] = None


class Colleague(BaseModel):
    id: str
    name: str
    instruction: str
    allowed_users: Optional[List[str]] = ["*"]
    allowed_groups: Optional[List[str]] = []


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "M-Files AI Assistant Backend is running.", "version": "2.0.0"}


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    """
    Glavni chat endpoint. Sprejme conversation history in vrne odgovor od Clauda.
    """
    logger.info(f"Chat zahteva: model={request.model}, messages={len(request.messages or [])}")

    # Sestavi messages array za Claude
    if request.messages and len(request.messages) > 0:
        # Frontend poslal celotno conversaton history
        claude_messages = [{"role": m.role, "content": m.content} for m in request.messages]
    else:
        # Fallback: samo en query (stara kompatibilnost)
        claude_messages = [{"role": "user", "content": request.query}]

    # System prompt iz persona instrukcije
    system_prompt = request.persona_instruction or None

    try:
        reply = mcr_router.route_llm_call(
            model_name=request.model,
            messages=claude_messages,
            system_prompt=system_prompt,
        )
        logger.info("Odgovor uspešno generiran.")
    except Exception as e:
        logger.error(f"Napaka pri generiranju odgovora: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Napaka pri LLM generiranju: {str(e)}")

    return ChatResponse(reply=reply, model_used=request.model)


# ── Persistence API ──────────────────────────────────────────────────────────

@app.get("/api/history")
def get_history():
    return persistence.get_chats()


@app.post("/api/history")
def save_history(chat: Dict[str, Any]):
    persistence.save_chat(chat)
    return {"status": "success"}


@app.delete("/api/history/{chat_id}")
def delete_history(chat_id: str):
    persistence.delete_chat(chat_id)
    return {"status": "success"}


@app.get("/api/colleagues")
def get_colleagues():
    return persistence.get_colleagues()


@app.post("/api/colleagues")
def save_colleague(colleague: Dict[str, Any]):
    persistence.save_colleague(colleague)
    return {"status": "success"}


@app.delete("/api/colleagues/{colleague_id}")
def delete_colleague(colleague_id: str):
    persistence.delete_colleague(colleague_id)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)