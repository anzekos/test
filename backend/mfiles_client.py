import os
import logging
import requests
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

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

    def fetch_documents(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Pridobi dokumente iz M-Files. V produkciji bi tu uporabili iskalni API.
        Zaradi demonstracije vrnemo mock strukturo, če ni povezave.
        """
        if not self.token and not self.authenticate():
            logger.info("Uporabljam mock dokumente za M-Files (ni povezave).")
            return [
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

        # Primer pravega klica (prilagodi glede na točno shemo M-Files)
        headers = {"X-Authentication": self.token}
        search_url = f"{self.base_url}/objects?q={query}"
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Tu bi parsirali in prenesli vsebino datotek iz M-Files
                # Za zdaj vrnemo simulacijo parsiranih podatkov
                logger.info("Uspešno preneseni metapodatki iz M-Files.")
                return []
            else:
                logger.error(f"Napaka iskanja M-Files: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Napaka pri klicu M-Files: {e}")
            return []

mfiles_client = MFilesClient()
