import os
import hashlib
import struct
import logging
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

load_dotenv()
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_db")
        self.qdrant_client = QdrantClient(path=self.qdrant_path)
        self.sidecar_url = os.getenv("EMBEDDING_SIDECAR_URL", "http://127.0.0.1:8001")

        # multilingual-e5-large = 1024 dims
        self.vector_size = 1024

        self._wait_for_sidecar()
        self._ensure_collections()
        logger.info("VectorStore inicializiran s Qdrant in sidecarjem multilingual-e5-large.")

    def _wait_for_sidecar(self):
        import requests as req
        logger.info(f"Čakam na sidecar na {self.sidecar_url}...")
        for i in range(30):
            try:
                resp = req.get(f"{self.sidecar_url}/health", timeout=2)
                if resp.status_code == 200:
                    logger.info("Sidecar dosegljiv.")
                    return
            except req.exceptions.RequestException:
                pass
            time.sleep(1)
            if i % 5 == 0:
                logger.info("Sidecar še ni dosegljiv...")
        logger.warning("Sidecar ni dosegljiv — embedding bo padel na dummy.")

    def _ensure_collections(self):
        collections = self.qdrant_client.get_collections().collections
        existing = {c.name for c in collections}

        for name in ["mfiles_collection", "pirs_collection"]:
            if name in existing:
                try:
                    info = self.qdrant_client.get_collection(name)
                    if info.config.params.vectors.size != self.vector_size:
                        logger.warning(
                            f"Kolekcija '{name}' ima dimenzijo "
                            f"{info.config.params.vectors.size}, pričakujem {self.vector_size}. "
                            "Brišem in ustvarjam novo."
                        )
                        self.qdrant_client.delete_collection(name)
                        existing.discard(name)
                except Exception as e:
                    logger.error(f"Napaka pri preverjanju kolekcije '{name}': {e}")

            if name not in existing:
                self.qdrant_client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Ustvarjena kolekcija '{name}' (dim={self.vector_size}).")

    def _dummy_embedding(self, text: str) -> List[float]:
        """
        Deterministični dummy embedding — dimenzija = self.vector_size.
        FIX: prej je bilo hardkodiranih 1536, zdaj pravilno 1024 za e5-large.
        """
        h = hashlib.sha512(text.encode("utf-8")).digest()
        needed_bytes = self.vector_size * 4
        repeated = (h * ((needed_bytes // len(h)) + 1))[:needed_bytes]
        values = struct.unpack(f"{self.vector_size}f", repeated)
        max_abs = max(abs(v) for v in values) or 1.0
        return [v / max_abs for v in values]

    def embed_text(self, text: str, is_query: bool = False) -> List[float]:
        import requests as req
        try:
            resp = req.post(
                f"{self.sidecar_url}/embed",
                json={"texts": [text], "is_query": is_query},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("embeddings"):
                return data["embeddings"][0]
        except Exception as e:
            logger.warning(f"Sidecar embedding napaka, padec na dummy: {e}")
        return self._dummy_embedding(text)

    def collection_count(self, name: str) -> int:
        return self.qdrant_client.count(collection_name=name).count

    def upsert_batch(self, collection_name: str, items: List[Dict[str, Any]]):
        points = []
        for item in items:
            vector = self.embed_text(item["content"], is_query=False)
            points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, item["id"])),
                vector=vector,
                payload={"content": item["content"], **item.get("metadata", {})},
            ))
        if points:
            self.qdrant_client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Upsert {len(points)} točk v '{collection_name}'.")

    def upsert_document(self, collection_name: str, doc_id: str, content: str, metadata: Dict[str, Any]):
        vector = self.embed_text(content, is_query=False)
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=[PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id)),
                vector=vector,
                payload={"content": content, **metadata},
            )],
        )
        logger.debug(f"Dokument '{doc_id}' upsertan v '{collection_name}'.")

    def search(self, collection_name: str, query: str, top_k: int = 3) -> List[Dict]:
        try:
            query_vector = self.embed_text(query, is_query=True)
            hits = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
            )
            return [hit.payload for hit in hits]
        except Exception as e:
            logger.error(f"Napaka pri iskanju v '{collection_name}': {e}")
            return []


# Singleton
vector_store = VectorStore()