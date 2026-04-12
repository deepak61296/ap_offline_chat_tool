import os
import json
import requests
import re
from typing import List, Dict

PARAM_URL = "https://autotest.ardupilot.org/Parameters/ArduCopter/apm.pdef.json"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "apm.pdef.json")

# Prefixes to deprioritize (secondary/simulation/display params)
DEPRIORITIZE_PREFIXES = ('SIM_', 'OSD', 'NTF_', 'LOG_', 'STAT_')
# Numbered variants (BATT2, BATT3, etc.) get lower priority than primary
NUMBERED_SUFFIX_PATTERN = re.compile(r'^([A-Z]+)(\d+)_')

# Common query -> preferred prefix mappings
QUERY_PREFIX_MAP = {
    'battery': ['BATT_', 'BATT2_'],
    'loiter': ['LOIT_', 'LOITER'],
    'rtl': ['RTL_'],
    'altitude': ['ALT_', 'RTL_ALT'],
    'motor': ['MOT_'],
    'compass': ['COMPASS_'],
    'gps': ['GPS_', 'EK3_GPS'],
    'barometer': ['BARO', 'GND_'],
    'accelerometer': ['INS_ACC', 'INS_'],
    'arming': ['ARMING_', 'ARM_'],
    'fence': ['FENCE_'],
    'failsafe': ['FS_', 'BATT_FS', 'RC_FS'],
}

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
        """Improved keyword matching with smart ranking."""
        if not self.params:
            return []

        query_lower = query.lower()
        query_terms = query_lower.split()
        results = []

        # Find preferred prefixes for this query
        preferred_prefixes = []
        for key, prefixes in QUERY_PREFIX_MAP.items():
            if key in query_lower:
                preferred_prefixes.extend(prefixes)

        for p in self.params:
            name = p["name"]
            name_lower = name.lower()
            score = 0

            # Check each query term
            for term in query_terms:
                # Exact name match (highest priority)
                if name_lower == term:
                    score += 20
                # Term in parameter name
                elif term in name_lower:
                    score += 5
                # Term in display name
                elif term in p["display_name"].lower():
                    score += 3
                # Term in description
                elif term in p["description"].lower():
                    score += 1

            if score == 0:
                continue

            # Boost: preferred prefix for this query type
            for prefix in preferred_prefixes:
                if name.startswith(prefix):
                    score += 8
                    break

            # Penalty: deprioritize SIM_, OSD, etc.
            if name.startswith(DEPRIORITIZE_PREFIXES):
                score -= 5

            # Penalty: numbered variants (BATT2_, BATT3_) rank lower than primary
            num_match = NUMBERED_SUFFIX_PATTERN.match(name)
            if num_match:
                variant_num = int(num_match.group(2))
                if variant_num > 1:
                    score -= (variant_num - 1) * 2

            results.append((score, p))

        # Sort by score descending, then by name length (shorter = more specific)
        results.sort(key=lambda x: (-x[0], len(x[1]["name"])))

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
