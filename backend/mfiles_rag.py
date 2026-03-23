import logging
from typing import List, Dict
from vector_store import vector_store
from mfiles_client import mfiles_client

logger = logging.getLogger(__name__)

class MFilesRetriever:
    def __init__(self):
        self.is_connected = True
        self.collection_name = "mfiles_collection"
        logger.info("M-Files Retriever inicializiran.")
        self._ensure_index()
        
    def _ensure_index(self):
        """Pomozna metoda, ki indeksira nekaj dokumentov ce zbirka se ni polna."""
        # V pravi aplikaciji bi imeli loceno logiko za background job, ki sinhronizira M-Files in Qdrant
        logger.info("Preverjam M-Files index...")
        docs = mfiles_client.fetch_documents()
        for doc in docs:
            metadata = {
                "source": f"M-Files ID: {doc['id']}",
                "filename": doc['filename']
            }
            try:
                vector_store.upsert_document(self.collection_name, str(doc['id']), doc['content'], metadata)
            except Exception as e:
                logger.warning(f"Ni bilo mogoce indeksirati v Qdrant (M-Files): {e}")

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Poizvedba po internih M-Files dokumentih odvetniške pisarne s pomocjo Vector baze
        """
        logger.info(f"M-Files Vektorsko iskanje za: '{query}'")
        
        try:
            results = vector_store.search(self.collection_name, query, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"Napaka pri vektorskem iskanju M-Files: {e}")
            return []

# Singleton
mf_rag = MFilesRetriever()
