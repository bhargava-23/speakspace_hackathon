import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Ensure directory exists
os.makedirs("data", exist_ok=True)

TRENDS_FILE = "data/trends.json"
REF_FILE = "data/page_refs.json"


# -----------------------------
# IDENTITY / IDEMPOTENCY LAYER
# -----------------------------
def note_exists(note_id: str) -> bool:
    """Return True if this note_id has already been processed."""
    if not os.path.exists(REF_FILE):
        return False
    try:
        with open(REF_FILE, "r") as f:
            refs = json.load(f)
        return note_id in refs
    except Exception:
        return False


def get_existing_page(note_id: str) -> str | None:
    """Return the existing Notion page URL for this note_id."""
    try:
        if not os.path.exists(REF_FILE):
            return None
        with open(REF_FILE, "r") as f:
            refs = json.load(f)
        return refs.get(note_id)
    except Exception:
        return None


def save_page_reference(note_id: str, page_url: str):
    """Store mapping: note_id → page_url."""
    try:
        if os.path.exists(REF_FILE):
            with open(REF_FILE, "r") as f:
                refs = json.load(f)
        else:
            refs = {}

        refs[note_id] = page_url

        with open(REF_FILE, "w") as f:
            json.dump(refs, f, indent=2)

        logger.info(f"Saved idempotency reference for note_id={note_id}")

    except Exception as e:
        logger.error(f"Failed saving page reference: {e}")


# -----------------------------
# PATTERN ANALYSIS LOGGING
# -----------------------------
def log_trend(note_id: str, extracted: dict, timestamp: str, user_id: str | None = None):
    """Record essential details for long-term insights."""
    try:
        tasks = extracted.get("tasks", [])
        vibes = [t.get("vibe", "neutral") for t in tasks]
        prios = [t.get("prio", "medium") for t in tasks]

        avg_priority = sum(
            1.0 if p == "high" else 0.5 if p == "medium" else 0.0
            for p in prios
        ) / max(len(prios), 1)

        dominant_vibe = max(set(vibes), key=vibes.count) if vibes else "neutral"

        entry = {
            "note_id": note_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "tasks_count": len(tasks),
            "avg_priority": round(avg_priority, 2),
            "dominant_vibe": dominant_vibe,
            "summary": extracted.get("summary", "")[:80]
        }

        if os.path.exists(TRENDS_FILE):
            with open(TRENDS_FILE, "r") as f:
                trends = json.load(f)
        else:
            trends = []

        trends.append(entry)

        # limit file growth
        with open(TRENDS_FILE, "w") as f:
            json.dump(trends[-200:], f, indent=2)

        logger.info(f"Trend logged for note_id={note_id}")

    except Exception as e:
        logger.error(f"Trend logging failed: {e}")


def get_insights(note_id: str | None = None) -> str:
    """Generate pattern insights for toggle block in Notion."""
    try:
        if not os.path.exists(TRENDS_FILE):
            return "History is empty — trends will appear after a few voice notes."

        with open(TRENDS_FILE, "r") as f:
            trends = json.load(f)

        if not trends:
            return "No trends yet — submit a few more notes."

        # If a specific note's insights requested
        if note_id:
            entry = next((t for t in trends if t["note_id"] == note_id), None)
            if entry:
                return (
                    f"{entry['tasks_count']} tasks · "
                    f"Priority score {entry['avg_priority']}/1.0 · "
                    f"Vibe: {entry['dominant_vibe']}"
                )

        # Global recent trends
        recent = trends[-10:]
        avg_tasks = sum(t["tasks_count"] for t in recent) / len(recent)
        stress_count = sum(1 for t in recent if t["dominant_vibe"] == "stressed")

        if stress_count >= 5:
            return f"Stress pattern detected in {stress_count}/10 recent notes."
        if avg_tasks > 6:
            return f"High workload trend: averaging {avg_tasks:.1f} tasks per note."
        if avg_tasks < 3:
            return f"Low task volume trend: averaging {avg_tasks:.1f} tasks per note."

        return f"Balanced trend: avg {avg_tasks:.1f} tasks per note."

    except Exception as e:
        logger.error(f"Trend insight generation failed: {e}")
        return "Trend insights unavailable."
