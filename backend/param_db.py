import os
import json
import requests
import re
from typing import List, Dict

PARAM_URL = "https://autotest.ardupilot.org/Parameters/ArduCopter/apm.pdef.json"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "apm.pdef.json")

class ParameterDB:
    def __init__(self):
        self.params: List[Dict] = []
        self._load_db()

    def _load_db(self):
        """Loads the param database from cache or downloads it."""
        if not os.path.exists(CACHE_FILE):
            print("[ParamDB] Downloading ArduCopter Parameter Database...")
            try:
                r = requests.get(PARAM_URL, timeout=10)
                r.raise_for_status()
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f)
            except Exception as e:
                print(f"[ParamDB] Failed to download parameter DB: {e}")
                return

        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Flatten the grouped parameters
        for group, params in raw_data.items():
            if isinstance(params, dict):
                for param_name, param_info in params.items():
                    if isinstance(param_info, dict):
                        # Create a unified string for searching
                        desc = param_info.get("Description", "")
                        dname = param_info.get("DisplayName", "")
                        
                        self.params.append({
                            "name": param_name,
                            "display_name": dname,
                            "description": desc,
                            "search_corpus": f"{param_name.lower()} {dname.lower()} {desc.lower()}"
                        })

    def search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Simple keyword matching to find the best parameter."""
        if not self.params:
            return []

        query_terms = query.lower().split()
        results = []

        for p in self.params:
            score = 0
            for term in query_terms:
                if term in p["name"].lower():
                    score += 3 # Exact parameter code match is highly weighted
                elif term in p["search_corpus"]:
                    score += 1
            
            if score > 0:
                results.append((score, p))

        # Sort by best score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Format the top K
        out = []
        for _, p in results[:top_k]:
            out.append({
                "name": p["name"],
                "description": p["description"]
            })
        return out

# Singleton instance
db = ParameterDB()

if __name__ == "__main__":
    print(db.search("battery failsafe"))
