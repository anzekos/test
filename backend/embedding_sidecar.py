import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Embedding Sidecar - Multilingual E5 Large")

# Naloži model ob zagonu
logger.info("Nalagam multilingual-e5-large model...")
try:
    model = SentenceTransformer('intfloat/multilingual-e5-large')
    logger.info("Model uspešno naložen.")
except Exception as e:
    logger.error(f"Napaka pri nalaganju modela: {e}")
    model = None

class EmbedRequest(BaseModel):
    texts: List[str]
    is_query: bool = False

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

@app.post("/embed", response_model=EmbedResponse)
def embed_texts(req: EmbedRequest):
    if not model:
        # Fallback za napake izven dosega uporabnika
        return EmbedResponse(embeddings=[])
        
    prefix = "query: " if req.is_query else "passage: "
    prefixed_texts = [prefix + text for text in req.texts]
    embeddings = model.encode(prefixed_texts, normalize_embeddings=True).tolist()
    return EmbedResponse(embeddings=embeddings)

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
