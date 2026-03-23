import os
import logging
import requests
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

MOCK_DOCUMENTS = [
    {
        "id": "15482",
        "filename": "Vzorec_Pogodbe_Zaposlitev_Standard_2026.docx",
        "content": "[Interni vzorec] 1. Člen: Delavec se zavezuje vestno in pravočasno opravljati delo. 5. Člen: Konkurenčna prepoved velja 2 leti po prenehanju."
    },
    {
        "id": "9021",
        "filename": "Interni_Pravilnik_Odvetn_Pisarna_v2",
        "content": "Za vsako novo stranko je potrebno opraviti KYC in identificirati morebiten konflikt interesov pred pričetkom dela."
    },
    {
        "id": "2241",
        "filename": "Splošni_Osnutek_Pravnega_Dokumenta.docx",
        "content": "Osnutek priporoča uporabo standardnih klavzul in napotitev na veljavno nacionalno zakonodajo."
    }
]

class MFilesClient:
    """
    Client za komunikacijo z M-Files REST API.
    """
    def __init__(self):
        self.base_url = os.getenv("MFILES_API_BASE_URL", "http://localhost:8080/REST")
        self.username = os.getenv("MFILES_USERNAME")
        self.password = os.getenv("MFILES_PASSWORD")
        self.vault_guid = os.getenv("MFILES_VAULT_GUID")
        self.token = None

    def authenticate(self) -> bool:
        """Pridobi avtentikacijski žeton za M-Files REST API."""
        if not all([self.username, self.password, self.vault_guid]):
            logger.warning("Manjkajo poverilnice za M-Files API v .env. MFilesClient bo deloval v mock načinu.")
            return False

        try:
            auth_url = f"{self.base_url}/server/authenticationtokens"
            payload = {
                "Username": self.username,
                "Password": self.password,
                "VaultGuid": self.vault_guid
            }
            response = requests.post(auth_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.token = response.json().get("Value")
                logger.info("Uspešno prijavljen v M-Files REST API.")
                return True
            else:
                logger.error(f"Napaka pri avtentikaciji M-Files: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Povezovalna napaka pri avtentikaciji M-Files: {e}")
            return False

    def _extract_text(self, raw_bytes: bytes) -> str:
        """Best-effort plain text extraction from raw file content."""
        try:
            return raw_bytes.decode("utf-8", errors="replace").strip()
        except Exception:
            return raw_bytes.decode("latin-1", errors="replace").strip()

    def fetch_documents(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Pridobi dokumente iz M-Files. V produkciji bi tu uporabili iskalni API.
        Zaradi demonstracije vrnemo mock strukturo, če ni povezave.
        """
        if not self.token and not self.authenticate():
            logger.info("Uporabljam mock dokumente za M-Files (ni povezave).")
            return MOCK_DOCUMENTS

        headers = {"X-Authentication": self.token}

        try:
            # 1. Fetch object list
            search_url = f"{self.base_url}/objects?q={query}"
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Napaka iskanja M-Files: {response.text}")
                return MOCK_DOCUMENTS

            items = response.json().get("Items", [])
            if not items:
                logger.info("M-Files ni vrnil nobenega objekta.")
                return MOCK_DOCUMENTS

            documents = []
            for obj in items:
                obj_id = obj.get("ObjVer", {}).get("ID")
                obj_version = obj.get("ObjVer", {}).get("Version", 1)
                title = obj.get("Title", f"object_{obj_id}")
                if obj_id is None:
                    continue

                # 2. Fetch files for this object
                files_url = f"{self.base_url}/objects/0/{obj_id}/{obj_version}/files"
                try:
                    files_resp = requests.get(files_url, headers=headers, timeout=10)
                    if files_resp.status_code != 200:
                        logger.warning(f"Ne morem pridobiti datotek za objekt {obj_id}")
                        continue
                    files = files_resp.json()
                except Exception as e:
                    logger.warning(f"Napaka pri pridobivanju datotek za objekt {obj_id}: {e}")
                    continue

                for file_info in files:
                    file_id = file_info.get("ID")
                    file_name = file_info.get("Name", title)
                    if file_id is None:
                        continue

                    # 3. Download file content
                    content_url = (
                        f"{self.base_url}/objects/0/{obj_id}/{obj_version}"
                        f"/files/{file_id}/content"
                    )
                    try:
                        content_resp = requests.get(
                            content_url, headers=headers, timeout=30
                        )
                        if content_resp.status_code != 200:
                            logger.warning(f"Ne morem prenesti vsebine datoteke {file_id}")
                            continue
                        text = self._extract_text(content_resp.content)
                    except Exception as e:
                        logger.warning(f"Napaka pri prenosu datoteke {file_id}: {e}")
                        continue

                    documents.append({
                        "id": str(obj_id),
                        "filename": file_name,
                        "content": text,
                    })

            if not documents:
                logger.info("Nobena datoteka ni bila uspešno prenesena; uporabljam mock.")
                return MOCK_DOCUMENTS

            logger.info(f"Uspešno prenesenih {len(documents)} dokumentov iz M-Files.")
            return documents

        except Exception as e:
            logger.error(f"Napaka pri klicu M-Files: {e}")
            return MOCK_DOCUMENTS

mfiles_client = MFilesClient()
