"""
ingest_pirs.py — Standalone script to populate Qdrant pirs_collection.

Usage:
    cd backend
    python ingest_pirs.py
"""
import logging
import re
import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PIRS_LAW_IDS = {
    "OZ":    "350848629",
    "ZDR-1": "",
    "ZPP":   "",
    "ZGD-1": "",
    "ZIZ":   "",
    "SPZ":   "",
    "KZ-1":  "",
    "ZKP":   "",
    "ZN":    "",
    "ZVPot-1": "",
    "ZLS":   "",
    "ZUstS": "",
}

def fetch_and_chunk_law(abbreviation: str, internal_id: str) -> list:
    if not internal_id:
        logger.warning(f"Ne morem prenesti {abbreviation}, ker ID manjka.")
        return []

    url = f"https://pisrs.si/api/datoteke/integracije/{internal_id}"
    try:
        logger.info(f"Prenašam zakon {abbreviation} iz {url}...")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        text = resp.text
        
        # Razdeli tekst z regex: \n\d+. člen
        # Regex uporabi capture group obdelavo, ali finditer za ohranitev številke člena.
        # Enostaven split ne ohrani separatorja, zato uporabimo capture s split ali pa finditer.
        
        pattern = re.compile(r'\n(\d+)\.\s+člen', re.IGNORECASE)
        parts = pattern.split(text)
        
        chunks = []
        
        # Text pred prvim členom (uvod/splošno), vzamemo kot chunk 0 (ali ga spustimo).
        # parts[0] = tekst pred 1. členom
        # parts[1] = številka člena 1
        # parts[2] = vsebina člena 1 ...
        
        # Če želimo shraniti tudi uvodne določbe:
        if parts[0].strip():
            chunks.append({
                "id": f"{abbreviation}_uvod",
                "content": parts[0].strip(),
                "metadata": {
                    "source": abbreviation,
                    "section": "Uvodne določbe"
                }
            })
            
        for i in range(1, len(parts), 2):
            clen_number = parts[i]
            # Vsebina člena vključuje številko člena in preostanek teksta.
            # Za večjo jasnost dodamo številko člena nazaj v content oz. uporabimo v metapodatkih.
            clen_content = f"{clen_number}. člen\n{parts[i+1]}".strip()
            
            chunks.append({
                "id": f"{abbreviation}_clen_{clen_number}",
                "content": clen_content,
                "metadata": {
                    "source": abbreviation,
                    "section": f"Člen {clen_number}"
                }
            })
            
        logger.info(f"{abbreviation} uspešno razdeljen na {len(chunks)} odsekov.")
        return chunks

    except Exception as e:
        logger.error(f"Napaka pri obdelavi zakona {abbreviation}: {e}")
        return []

def main():
    from vector_store import vector_store

    collection = "pirs_collection"
    all_chunks = []

    for law_abbr, law_id in PIRS_LAW_IDS.items():
        if law_id:
            law_chunks = fetch_and_chunk_law(law_abbr, law_id)
            all_chunks.extend(law_chunks)

    if not all_chunks:
        logger.warning("Noben zakon ni bil prenesen (manjkajoči ID-ji?). Preklicujem indeksiranje.")
        return

    logger.info(f"Shranjujem {len(all_chunks)} PIRS odsekov v '{collection}'...")
    # Preden pošljemo batch, preverimo, če jih je preveč in naredimo pod-batche
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        vector_store.upsert_batch(collection, all_chunks[i:i+batch_size])

    count = vector_store.collection_count(collection)
    logger.info(f"Končano. Zbirka '{collection}' zdaj vsebuje {count} zapisov.")

if __name__ == "__main__":
    main()
