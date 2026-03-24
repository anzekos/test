import os
import hashlib
import struct
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

load_dotenv()
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY missing. Using deterministic dummy embeddings.")
            
        # Using a local file-based Qdrant by default (path: ./qdrant_db)
        # In production this might be a remote cluster url
        self.qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_db")
        self.qdrant_client = QdrantClient(path=self.qdrant_path)
        
        # Dimensions for intfloat/multilingual-e5-large
        self.vector_size = 1024
        self.sidecar_url = os.getenv("EMBEDDING_SIDECAR_URL", "http://127.0.0.1:8001")
        
        # Verify sidecar is up first
        self._wait_for_sidecar()

        self._ensure_collections()
        logger.info("VectorStore inicializiran s Qdrant in sidecarjem multilingual-e5-large.")

    def _wait_for_sidecar(self):
        import time
        import requests
        max_retries = 30
        logger.info(f"Preverjam dosegljivost sidecarja na {self.sidecar_url}...")
        for i in range(max_retries):
            try:
                resp = requests.get(f"{self.sidecar_url}/health", timeout=2)
                if resp.status_code == 200:
                    logger.info("Sidecar uspešno dosegljiv.")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
            if i % 5 == 0:
                logger.info("Čakam na start sidecarja...")
        logger.warning("Sidecar ni dosegljiv, vector_store morda ne bo deloval pravilno.")

    def _ensure_collections(self):
        """Preveri in ustvari M-Files in PIRS zbirki v Qdrant-u, če ne obstajata."""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        for name in ["mfiles_collection", "pirs_collection"]:
            if name in collection_names:
                try:
                    col_info = self.qdrant_client.get_collection(collection_name=name)
                    # Preveri dimenzije
                    if col_info.config.params.vectors.size != self.vector_size:
                        logger.warning(f"Zbirka {name} ima napačno dimenzijo vektorjev {col_info.config.params.vectors.size}. Brišem zbirko, ker pričakujem {self.vector_size}.")
                        self.qdrant_client.delete_collection(collection_name=name)
                        collection_names.remove(name)
                except Exception as e:
                    logger.error(f"Napaka pri branju zbirke {name}: {e}")
            
            if name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Ustvaril novo Qdrant zbirko: {name}")

    def _dummy_embedding(self, text: str) -> List[float]:
        """Deterministic 1536-dim dummy embedding derived from SHA-512 hash of text."""
        h = hashlib.sha512(text.encode("utf-8")).digest()
        # Repeat hash bytes to fill 1536 floats (1536 * 4 = 6144 bytes needed)
        repeated = h * ((6144 // len(h)) + 1)
        values = struct.unpack(f"{self.vector_size}f", repeated[: self.vector_size * 4])
        # Normalize to [-1, 1] range
        max_abs = max(abs(v) for v in values) or 1.0
        return [v / max_abs for v in values]

    def embed_text(self, text: str, is_query: bool = False) -> List[float]:
        """Ustvari vektor za podan tekst z uporabo lokalnega sidecar servisa."""
        import requests
        try:
            payload = {"texts": [text], "is_query": is_query}
            resp = requests.post(f"{self.sidecar_url}/embed", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data and data.get("embeddings") and len(data["embeddings"]) > 0:
                return data["embeddings"][0]
        except Exception as e:
            logger.error(f"Napaka pri klicu embedding sidecarja: {e}")
        
        logger.debug("Opozorilo: Uporabljam dummy embedding kot fallback!")
        return self._dummy_embedding(text)

    def collection_count(self, name: str) -> int:
        """Return the number of points in a given collection."""
        return self.qdrant_client.count(collection_name=name).count

    def upsert_batch(self, collection_name: str, items: List[Dict[str, Any]]):
        """Batch upsert a list of {id, content, metadata} dicts into a collection."""
        points = []
        for item in items:
            vector = self.embed_text(item["content"], is_query=False)
            point = PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, item["id"])),
                vector=vector,
                payload={"content": item["content"], **item.get("metadata", {})},
            )
            points.append(point)

        if points:
            self.qdrant_client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Batch upserted {len(points)} points into {collection_name}")

    def upsert_document(self, collection_name: str, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Doda ali posodobi dokument v izbrani zbirki."""
        vector = self.embed_text(content, is_query=False)
        
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
            query_vector = self.embed_text(query, is_query=True)
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
