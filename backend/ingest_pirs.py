"""
ingest_pirs.py — Polni Qdrant pirs_collection z zakonodajo iz pisrs.si.

Zaženi enkrat (ali ob posodobitvah zakonodaje):
    cd backend
    python ingest_pirs.py

Kako deluje (brez Playwrighta, brez ELI):
    1. Za vsak zakon pokliče:
       GET https://pisrs.si/api/rezultat/zbirka/id/{ZAKO_CODE}
       → vrne JSON z vsemi NPB verzijami in njihovimi file ID-ji (isto kot zako5944.json)
    2. Iz JSON-a vzame najnovejšo NPB verzijo → HTML_DOCUMENT file ID
    3. Pokliče:
       GET https://pisrs.si/api/datoteke/integracije/{file_id}
       → vrne plain text celotnega zakona
    4. Razdeli po členih z regex \n\d+. člen
    5. Shrani v Qdrant z metapodatki (vir, člen)
"""

import re
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ZAKO kode za vseh 12 zakonov (iz get_pirs_ids.py + potrjen OZ)
# Koda je stabilen identifikator zakona na pisrs.si
PIRS_LAWS = {
    "OZ":      "ZAKO1263",   # Obligacijski zakonik
    "ZDR-1":   "ZAKO5944",   # Zakon o delovnih razmerjih ✓ (potrjeno iz zako5944.json)
    "ZPP":     "ZAKO3210",   # Zakon o pravdnem postopku
    "ZGD-1":   "ZAKO4291",   # Zakon o gospodarskih družbah
    "ZIZ":     "ZAKO3351",   # Zakon o izvršbi in zavarovanju
    "SPZ":     "ZAKO3242",   # Stvarnopravni zakonik
    "KZ-1":    "ZAKO5019",   # Kazenski zakonik
    "ZKP":     "ZAKO1588",   # Zakon o kazenskem postopku
    "ZN":      "ZAKO1198",   # Zakon o notariatu
    "ZVPot-1": "ZAKO7840",   # Zakon o varstvu potrošnikov
    "ZLS":     "ZAKO408",    # Zakon o lokalni samoupravi
    "ZUstS":   "ZAKO1260",   # Zakon o Ustavnem sodišču
}

PISRS_API = "https://pisrs.si/api/rezultat/zbirka/id/{zako}"
PISRS_TEXT = "https://pisrs.si/api/datoteke/integracije/{file_id}"


def get_latest_html_file_id(zako_code: str) -> str | None:
    """
    Pokliče pisrs.si API za zakon in vrne file ID najnovejšega
    HTML_DOCUMENT (enako kot zako5944.json za ZDR-1).
    """
    url = PISRS_API.format(zako=zako_code)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"  {zako_code}: napaka pri klicu API: {e}")
        return None

    datoteke = data.get("data", {}).get("datoteke", [])
    if not datoteke:
        logger.warning(f"  {zako_code}: API ni vrnil nobene datoteke.")
        return None

    # Najdi najnovejšo NPB verzijo
    # Vsaka verzija ima "npbVerzija": {"naziv": "NPB 14", ...} in seznam datotek
    # Vzamemo tisto z najvišjo številko NPB, ali "Osnovni" če NPB ni
    best_version = None
    best_npb_num = -1

    for verzija in datoteke:
        naziv = verzija.get("npbVerzija", {}).get("naziv", "")
        match = re.search(r"NPB\s*(\d+)", naziv, re.IGNORECASE)
        npb_num = int(match.group(1)) if match else 0

        if npb_num > best_npb_num:
            best_npb_num = npb_num
            best_version = verzija

    if best_version is None:
        best_version = datoteke[0]

    # Iz izbrane verzije vzemi HTML_DOCUMENT file ID
    for file_entry in best_version.get("datoteke", []):
        if file_entry.get("tip") == "HTML_DOCUMENT":
            file_id = file_entry.get("id")
            logger.info(f"  {zako_code}: NPB {best_npb_num}, HTML file ID = {file_id}")
            return str(file_id)

    logger.warning(f"  {zako_code}: HTML_DOCUMENT ni najden v NPB {best_npb_num}.")
    return None


def fetch_law_text(file_id: str) -> str:
    """Prenese plain text zakona iz pisrs.si/api/datoteke/integracije/{id}."""
    url = PISRS_TEXT.format(file_id=file_id)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def chunk_by_clen(text: str, abbreviation: str) -> list:
    """
    Razdeli besedilo zakona na chunke po vzorcu '\nN. člen'.
    Vsak chunk dobi metapodatke: source, section (člen).
    """
    pattern = re.compile(r"\n(\d+[a-z]?)\.\s+člen", re.IGNORECASE)
    parts = pattern.split(text)

    chunks = []

    # Uvodni del pred prvim členom
    if parts[0].strip():
        chunks.append({
            "id": f"{abbreviation}_uvod",
            "content": parts[0].strip(),
            "metadata": {"source": abbreviation, "section": "Uvodne določbe"},
        })

    # Vsak člen
    for i in range(1, len(parts), 2):
        clen_num = parts[i]
        if i + 1 >= len(parts):
            break
        clen_body = parts[i + 1].strip()
        if not clen_body:
            continue
        chunks.append({
            "id": f"{abbreviation}_clen_{clen_num}",
            "content": f"{clen_num}. člen\n{clen_body}",
            "metadata": {"source": abbreviation, "section": f"Člen {clen_num}"},
        })

    return chunks


def main():
    from vector_store import vector_store

    collection = "pirs_collection"
    all_chunks = []

    logger.info(f"Začenjam PIRS ingestion za {len(PIRS_LAWS)} zakonov...")

    for abbreviation, zako_code in PIRS_LAWS.items():
        logger.info(f"Obdelujem {abbreviation} ({zako_code})...")

        file_id = get_latest_html_file_id(zako_code)
        if not file_id:
            logger.warning(f"  {abbreviation}: preskoči (ni file ID).")
            continue

        try:
            text = fetch_law_text(file_id)
        except Exception as e:
            logger.error(f"  {abbreviation}: napaka pri prenosu teksta: {e}")
            continue

        chunks = chunk_by_clen(text, abbreviation)
        logger.info(f"  {abbreviation}: {len(chunks)} chunkov.")
        all_chunks.extend(chunks)

    if not all_chunks:
        logger.error("Ni chunkov za indeksiranje. Preveri internetno povezavo in ZAKO kode.")
        return

    logger.info(f"Shranjujem {len(all_chunks)} chunkov v Qdrant...")

    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        vector_store.upsert_batch(collection, batch)
        logger.info(f"  Batch {i // batch_size + 1}: {len(batch)} chunkov shranjenih.")

    count = vector_store.collection_count(collection)
    logger.info(f"Ingestion zaključen. '{collection}' vsebuje {count} zapisov.")


if __name__ == "__main__":
    main()