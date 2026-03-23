import os
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMRouter:
    def __init__(self):
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        
    def generate_response(self, query: str, model_name: str, context: List[str]) -> str:
        """
        Združi prejet kontekst iz RAG-a z vprašanjem in ga pošlje
        specifičnemu LLM modelu za generiranje odgovora.
        """
        context_text = "\n\n".join(context)
        
        prompt = (
            "Deluješ kot strokovni pravni asistent znotraj sistema M-Files.\n"
            "Spodaj so podani relevantni viri (Zakonodaja / Interni dokumenti):\n"
            "--------------------------------------------------\n"
            f"{context_text}\n"
            "--------------------------------------------------\n\n"
            f"Vprašanje uporabnika: {query}\n\n"
            "Strokovni odgovor (odgovori v ustrezno strukturiranem Markdown formatu in citiraj vire, če so relevantni):"
        )
        
        try:
            if model_name.lower() == "claude":
                return self._call_claude(prompt)
            elif model_name.lower() == "gemini":
                return self._call_gemini(prompt)
            elif model_name.lower() == "mistral":
                return self._call_mistral(prompt)
            else:
                return f"Napaka: Neznan model '{model_name}'"
        except Exception as e:
            logger.error(f"Napaka pri klicu modela {model_name}: {e}")
            return f"Prišlo je do napake pri komunikaciji z modelom {model_name}. Prosimo preverite API ključe v .env datoteki ali loge."

    def _call_claude(self, prompt: str) -> str:
        if not self.claude_key:
            return "**[Claude Mock]** API ključ (ANTHROPIC_API_KEY) ni na voljo v `.env`.\n\nSimuliran odgovor:\nSistemu bi predlagal natančno pregledovanje vira pri pripravi dokumentov. Na podlagi posredovanih informacij:\n\n*   Uporabljene naj bodo določbe iz **ZDR-1**.\n*   Upoštevati je potrebno **interne vzorce pogodbe**.\n\n*Zavrnitev odgovornosti: To je simuliran odgovor, saj sistem nima nastavljenega Anthropic ključa.*"
        
        import anthropic
        client = anthropic.Anthropic(api_key=self.claude_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _call_gemini(self, prompt: str) -> str:
        if not self.gemini_key:
            return "**[Gemini Mock]** API ključ (GEMINI_API_KEY) ni na voljo v `.env`.\n\nSimuliran odgovor:\nIzkoriščam veliko kontekstno okno. Glede na M-Files dokumente in strokovno prakso:\n\n1.  **KYC in konflikt interesov**: Vedno upoštevaj interni pravilnik.\n2.  **Pogodbene klavzule**: Smiselno je vključiti konkurenčno prepoved.\n\n*To je zgolj testni odgovor.*"
            
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        return response.text

    def _call_mistral(self, prompt: str) -> str:
        if not self.mistral_key:
            return "**[Mistral Mock]** API ključ (MISTRAL_API_KEY) ni na voljo v `.env`.\n\nKot evropski AI model potrjujem:\n\n> Interno določen KYC postopek v celoti izpolnjuje zahteve *GDPR* in EU regulativ.\n\n*Testni output, Mistral API ključ manjka.*"
            
        from mistralai.client import MistralClient
        from mistralai.models.chat_completion import ChatMessage
        client = MistralClient(api_key=self.mistral_key)
        messages = [ChatMessage(role="user", content=prompt)]
        chat_response = client.chat(model="mistral-large-latest", messages=messages)
        return chat_response.choices[0].message.content

# Singleton instanca za naš API
mcr_router = LLMRouter()
