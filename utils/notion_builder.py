import os
import time
import logging
from typing import Dict, Any
from notion_client import Client

from .trends import get_insights

logger = logging.getLogger(__name__)

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DB_ID = os.getenv("NOTION_DATABASE_ID")

def notion_retry(func):
    """Retries Notion calls 3 times with exponential backoff."""
    def wrapper(*args, **kwargs):
        delay = 1
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning(f"Notion retry {attempt+1}/3 after error: {e}")
                time.sleep(delay)
                delay *= 2
    return wrapper

@notion_retry
def _create_page(properties):
    return notion.pages.create(parent={"database_id": DB_ID}, properties=properties)

@notion_retry
def _append_blocks(page_id, blocks):
    return notion.blocks.children.append(block_id=page_id, children=blocks)

def create_page(extracted: Dict[str, Any], note_id: str, timestamp: str, user_id: str | None) -> str:
    tasks = extracted.get("tasks", [])
    summary = extracted.get("summary", "Voice Note")
    insights = extracted.get("insights", "")

    vibes = [t.get("vibe", "neutral") for t in tasks]
    dominant_vibe = max(set(vibes), key=vibes.count)

    # ---------- PAGE PROPERTIES + AUDIT TRAIL ----------
    properties = {
        "Name": {"title": [{"text": {"content": summary[:100]}}]},
        "Vibe": {"select": {"name": dominant_vibe}},
        "Source": {"rich_text": [{"text": {"content": f"Voice Note #{note_id}"}}]},
        "Audit Trail": {     # ⭐ WOW FACTOR
            "rich_text": [{
                "text": {
                    "content": f"NoteID: {note_id} | Timestamp: {timestamp} | User: {user_id}"
                }
            }]
        }
    }

    # CREATE PAGE
    new_page = _create_page(properties)
    page_id = new_page["id"]
    page_url = f"https://www.notion.so/{page_id.replace('-', '')}"

    blocks = []

    # ---------- INSIGHT CALLOUT ----------
    vibe_icon = {"stressed": "😰", "pumped": "🚀", "neutral": "💡"}.get(dominant_vibe, "💡")
    blocks.append({
        "type": "callout",
        "callout": {
            "rich_text": [{"text": {"content": insights}}],
            "icon": {"emoji": vibe_icon}
        }
    })

    # ---------- TASK LIST ----------
    blocks.append({
        "type": "heading_2",
        "heading_2": {"rich_text": [{"text": {"content": "Action Items"}}]}
    })

    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    for t in tasks:
        txt = f"{emoji[t['prio']]} {t['name']}"
        if t.get("due"):
            txt += f" (Due: {t['due']})"
        blocks.append({
            "type": "to_do",
            "to_do": {
                "rich_text": [{"text": {"content": txt}}],
                "checked": False
            }
        })

    # ---------- PATTERN ANALYSIS ----------
    blocks.append({
        "type": "toggle",
        "toggle": {
            "rich_text": [{"text": {"content": "📊 Pattern Analysis"}}],
            "children": [{
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": get_insights(note_id)}}]
                }
            }]
        }
    })

    _append_blocks(page_id, blocks)
    logger.info(f"[Notion] Page created: {page_url}")

    return page_url
