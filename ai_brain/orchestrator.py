import threading
import requests
import json
import re

class AITacticalBrain:
    def __init__(self, model_name="phi3"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model_name
        self.is_calculating = False

    def request_tactics_async(self, player_profile, dragon_instance):
        """Spawns a thread so the game doesn't stutter."""
        if self.is_calculating:
            return
        self.is_calculating = True
        threading.Thread(target=self._fetch_and_parse, args=(player_profile, dragon_instance)).start()

    def _fetch_and_parse(self, profile, dragon_instance):
        prompt = f"""
        You are a game AI. Player data: {profile}.
        Output ONLY a JSON dictionary assigning tactical weights (1-10) to these attacks:
        "fire_blast", "spike_drop", "earthquake".
        Example: {{"projectiles": 8, "spike_drop": 2, "earthquake": 4}}
        """
        
        try:
            response = requests.post(self.url, json={"model": self.model, "prompt": prompt, "stream": False})
            raw_text = response.json().get("response", "")
            
            match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
            if match:
                tactics = json.loads(match.group(0))
                dragon_instance.update_tactics(tactics)
                print(f"[AI DM] New Tactics Deployed: {tactics}")
            else:
                print("[AI ERROR] Failed to parse JSON. Falling back to default.")
                
        except Exception as e:
            print(f"[NETWORK ERROR] Local LLM unreachable: {e}")
            
        finally:
            self.is_calculating = False