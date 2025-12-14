import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

TRENDS_FILE = "data/trends.json"
MAPPING_FILE = "data/page_map.json"

os.makedirs("data", exist_ok=True)

def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def note_exists(note_id: str) -> bool:
    mapping = _load_json(MAPPING_FILE, {})
    return note_id in mapping

def save_page_reference(note_id: str, page_url: str):
    mapping = _load_json(MAPPING_FILE, {})
    mapping[note_id] = page_url
    _save_json(MAPPING_FILE, mapping)

def get_existing_page(note_id: str) -> str | None:
    mapping = _load_json(MAPPING_FILE, {})
    return mapping.get(note_id)

def log_trend(note_id: str, extracted: Dict[str, Any], timestamp: str, user_id: str | None):
    """Logs patterns + stores audit trail metadata."""
    trends = _load_json(TRENDS_FILE, [])

    tasks = extracted.get("tasks", [])
    vibes = [t.get("vibe", "neutral") for t in tasks]
    prios = [t.get("prio", "medium") for t in tasks]

    avg_prio = sum(1.0 if p == "high" else 0.5 if p == "medium" else 0.0 for p in prios) / max(len(prios), 1)
    dominant_vibe = max(set(vibes), key=vibes.count)

    entry = {
        "note_id": note_id,
        "timestamp": timestamp,
        "user_id": user_id,
        "tasks_count": len(tasks),
        "avg_priority": avg_prio,
        "dominant_vibe": dominant_vibe,
        "summary": extracted.get("summary", "")[:200]
    }

    trends.append(entry)
    _save_json(TRENDS_FILE, trends[-100:])
    logger.info(f"[Trend] {note_id} logged (user={user_id})")
