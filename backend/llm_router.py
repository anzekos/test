import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class LLMRouter:
    """Preprost router za Claude API klice s podporo za multi-turn conversation."""

    def __init__(self):
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")

    def route_llm_call(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Pošlje multi-turn sporočila na izbrani LLM.
        
        Args:
            model_name: ime modela ("claude", "gemini", "mistral")
            messages: seznam sporočil [{"role": "user"|"assistant", "content": "..."}]
            system_prompt: opcijski system prompt (persona instrukcija)
        """
        try:
            if model_name.lower() == "claude":
                return self._call_claude(messages, system_prompt)
            else:
                return f"Model '{model_name}' trenutno ni podprt. Uporabite 'claude'."
        except Exception as e:
            logger.error(f"Napaka pri klicu modela {model_name}: {e}", exc_info=True)
            return f"Prišlo je do napake pri komunikaciji z modelom {model_name}: {str(e)}"

    def _call_claude(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        if not self.claude_key:
            return (
                "**Napaka:** ANTHROPIC_API_KEY ni nastavljen v `.env` datoteki.\n\n"
                "Prosim ustvari datoteko `backend/.env` z vrstico:\n"
                "`ANTHROPIC_API_KEY=sk-ant-...`"
            )

        import anthropic

        client = anthropic.Anthropic(api_key=self.claude_key)

        # Privzeti system prompt
        default_system = (
            "Si prijazen in strokoven AI asistent integriran v M-Files. "
            "Odgovarjaš v slovenščini, razen če uporabnik piše v drugem jeziku. "
            "Odgovori naj bodo jasni, strukturirani in koristni."
        )

        system = system_prompt if system_prompt else default_system

        # Klic Claude Messages API
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=messages,
        )

        return response.content[0].text


# Singleton instanca
mcr_router = LLMRouter()
