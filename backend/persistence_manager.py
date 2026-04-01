import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

MAX_CHATS = 10

class PersistenceManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump({"chats": [], "colleagues": []}, f, ensure_ascii=False, indent=2)

    def load_data(self) -> Dict[str, Any]:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading persistence data: {e}")
            return {"chats": [], "colleagues": []}

    def save_data(self, data: Dict[str, Any]):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving persistence data: {e}")

    # CHATS
    def get_chats(self) -> List[Dict[str, Any]]:
        return self.load_data().get("chats", [])

    def save_chat(self, chat: Dict[str, Any]):
        data = self.load_data()
        chats = data.get("chats", [])
        
        # Check if chat exists and update, or append
        found = False
        for i, c in enumerate(chats):
            if c.get("id") == chat.get("id"):
                chats[i] = chat
                found = True
                break
        
        if not found:
            chats.insert(0, chat)

        # Ohrani samo zadnjih MAX_CHATS chattov
        data["chats"] = chats[:MAX_CHATS]
        self.save_data(data)

    def delete_chat(self, chat_id: str):
        data = self.load_data()
        data["chats"] = [c for c in data.get("chats", []) if c.get("id") != chat_id]
        self.save_data(data)

    # COLLEAGUES
    def get_colleagues(self) -> List[Dict[str, Any]]:
        return self.load_data().get("colleagues", [])

    def save_colleague(self, colleague: Dict[str, Any]):
        data = self.load_data()
        colleagues = data.get("colleagues", [])
        
        found = False
        for i, c in enumerate(colleagues):
            if c.get("id") == colleague.get("id"):
                colleagues[i] = colleague
                found = True
                break
        
        if not found:
            colleagues.append(colleague)
            
        data["colleagues"] = colleagues
        self.save_data(data)

    def delete_colleague(self, colleague_id: str):
        data = self.load_data()
        data["colleagues"] = [c for c in data.get("colleagues", []) if c.get("id") != colleague_id]
        self.save_data(data)

# Singleton instance
persistence = PersistenceManager(os.path.join(os.path.dirname(__file__), "persistence.json"))
