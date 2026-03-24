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
        
    def route_llm_call(self, model_name: str, query: str, context: List[str]) -> str:
        context_text = "\n\n".join(context)
        
        prompt = (
            "Ti si slovenski pravni asistent integriran v M-Files.\n"
            "OBVEZNA PRAVILA:\n"
            "1. Odgovarjaj IZKLJUČNO na podlagi virov v bloku <sources>. Ne uporabljaj lastnega znanja za nobeno pravno trditev.\n"
            "2. Vsako pravno trditev MORAŠ citirati v formatu: (ZPP, člen 105, odstavek 2).\n"
            "3. Če odgovora ni v virih, odgovori TOČNO: \"Priloženi pravni viri ne vsebujejo določbe za to vprašanje. Priporočamo posvet s specialistom.\"\n"
            "4. Nikoli ne sklepaj kaj zakon \"verjetno\" pravi.\n"
            "5. Vsak odgovor končaj z: \"Odgovor je informativne narave in ne predstavlja pravnega nasveta.\"\n\n"
            "<sources>\n"
            f"{context_text}\n"
            "</sources>\n\n"
            f"Vprašanje uporabnika: {query}\n"
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
