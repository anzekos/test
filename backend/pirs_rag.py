import logging
from typing import List, Dict
from vector_store import vector_store

logger = logging.getLogger(__name__)

class PIRSRetriever:
    def __init__(self):
        self.is_connected = True
        self.collection_name = "pirs_collection"
        logger.info("PIRS Retriever inicializiran z vektorsko bazo.")
        self._ensure_index()
        
    def _ensure_index(self):
        """Za demonstracijo uvozimo zacetno PIRS znanje v vektorsko bazo."""
        logger.info("Preverjam PIRS index...")
        mock_pirs_data = [
            {
                "id": "pirs_1",
                "source": "Zakon o delovnih razmerjih (ZDR-1)",
                "section": "Člen 11 in 31",
                "content": "Pogodba o zaposlitvi se sklene v pisni obliki. Vsebovati mora podatke o nazivu delovnega mesta, kraju opravljanja dela, času trajanja in odpovednem roku."
            },
            {
                "id": "pirs_2",
                "source": "Zakon o obligacijskih razmerjih (OZ)",
                "section": "Splošne določbe",
                "content": "Pogodba je sklenjena, ko se stranki zedinita o njenih bistvenih sestavinah."
            },
            {
                "id": "pirs_3",
                "source": "Zakon o pravdnem postopku (ZPP)",
                "section": "Splošne določbe",
                "content": "Sodišče odloča v mejah postavljenih zahtevkov. Vsaka stranka mora navesti dejstva in predlagati dokaze, na katere opira svoj zahtevek."
            }
        ]
        
        for item in mock_pirs_data:
            metadata = {
                "source": item["source"],
                "section": item["section"]
            }
            try:
                vector_store.upsert_document(self.collection_name, item["id"], item["content"], metadata)
            except Exception as e:
                logger.warning(f"Ni bilo mogoce indeksirati v Qdrant (PIRS): {e}")
                
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Poizvedba po PIRS (Pravno Informacijski Sistem / Strokovna baza).
        Vrne relevantne sekcije s pomocjo vektorskega iskanja.
        """
        logger.info(f"PIRS Vektorsko iskanje za: '{query}'")
        try:
            results = vector_store.search(self.collection_name, query, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"Napaka pri vektorskem iskanju PIRS: {e}")
            return []

# Singleton
pirs_rag = PIRSRetriever()
