import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

load_dotenv()
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY missing. Embeddings won't work.")
            
        # Using a local file-based Qdrant by default (path: ./qdrant_db)
        # In production this might be a remote cluster url
        self.qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_db")
        self.qdrant_client = QdrantClient(path=self.qdrant_path)
        
        # Dimensions for text-embedding-3-small
        self.vector_size = 1536
        
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        self._ensure_collections()
        logger.info("VectorStore inicializiran s Qdrant in text-embedding-3-small.")

    def _ensure_collections(self):
        """Preveri in ustvari M-Files in PIRS zbirki v Qdrant-u, če ne obstajata."""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        for name in ["mfiles_collection", "pirs_collection"]:
            if name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Ustvaril novo Qdrant zbirko: {name}")

    def embed_text(self, text: str) -> List[float]:
        """Ustvari vektor za podan tekst z uporabo OpenAI."""
        if not self.openai_client:
            raise ValueError("OpenAI API key ni nastavljen.")
            
        response = self.openai_client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def upsert_document(self, collection_name: str, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Doda ali posodobi dokument v izbrani zbirki."""
        vector = self.embed_text(content)
        
        point = PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id)), # Generator UUID
            vector=vector,
            payload={"content": content, **metadata}
        )
        
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        logger.debug(f"Dokument '{doc_id}' upsertan v {collection_name}")

    def search(self, collection_name: str, query: str, top_k: int = 3) -> List[Dict]:
        """Išče podobne dokumente v izbrani zbirki."""
        try:
            query_vector = self.embed_text(query)
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            
            results = []
            for hit in search_result:
                results.append(hit.payload)
            return results
        except Exception as e:
            logger.error(f"Napaka pri iskanju po {collection_name}: {e}")
            return []

# Singleton instanca za bazo
vector_store = VectorStore()
