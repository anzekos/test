"""
ingest_pirs.py — Standalone script to populate Qdrant pirs_collection.

Usage:
    cd backend
    python ingest_pirs.py
"""
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PIRS_CORPUS = [
    {
        "id": "pirs_1",
        "content": "Pogodba o zaposlitvi se sklene v pisni obliki. Vsebovati mora podatke o nazivu delovnega mesta, kraju opravljanja dela, času trajanja in odpovednem roku.",
        "metadata": {
            "source": "Zakon o delovnih razmerjih (ZDR-1)",
            "section": "Člen 11 in 31",
        },
    },
    {
        "id": "pirs_2",
        "content": "Pogodba je sklenjena, ko se stranki zedinita o njenih bistvenih sestavinah.",
        "metadata": {
            "source": "Zakon o obligacijskih razmerjih (OZ)",
            "section": "Splošne določbe",
        },
    },
    {
        "id": "pirs_3",
        "content": "Sodišče odloča v mejah postavljenih zahtevkov. Vsaka stranka mora navesti dejstva in predlagati dokaze, na katere opira svoj zahtevek.",
        "metadata": {
            "source": "Zakon o pravdnem postopku (ZPP)",
            "section": "Splošne določbe",
        },
    },
    {
        "id": "pirs_4",
        "content": "Delodajalec mora delavcu zagotoviti pogoje za varnost in zdravje pri delu v skladu s posebnim zakonom.",
        "metadata": {
            "source": "Zakon o delovnih razmerjih (ZDR-1)",
            "section": "Člen 45",
        },
    },
    {
        "id": "pirs_5",
        "content": "Pogodbena kazen je dogovorjena za primer, da dolžnik ne izpolni svoje obveznosti ali jo izpolni z zamudo.",
        "metadata": {
            "source": "Zakon o obligacijskih razmerjih (OZ)",
            "section": "Člen 247",
        },
    },
]


def main():
    from vector_store import VectorStore

    store = VectorStore()
    collection = "pirs_collection"

    logger.info(f"Ingesting {len(PIRS_CORPUS)} PIRS documents into '{collection}'...")
    store.upsert_batch(collection, PIRS_CORPUS)

    count = store.collection_count(collection)
    logger.info(f"Done. '{collection}' now contains {count} point(s).")


if __name__ == "__main__":
    main()
