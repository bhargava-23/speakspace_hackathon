import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq
from textblob import TextBlob
from dateutil import parser as date_parser

from .validators import ExtractedData, check_guardrails

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_TASKS = int(os.getenv("MAX_TASKS", 5))   # limit enforced after AI extraction


# -----------------------------
# Date Parsing Helper
# -----------------------------
def parse_fuzzy_date(date_str: str) -> str | None:
    if not date_str:
        return None

    try:
        parsed = date_parser.parse(date_str, fuzzy=True)
        return parsed.date().isoformat()
    except Exception:
        ds = date_str.lower().strip()
        today = datetime.now()

        if "tomorrow" in ds:
            return (today + timedelta(days=1)).date().isoformat()
        if "eod" in ds or "end of day" in ds:
            return today.date().isoformat()
        if "next week" in ds:
            return (today + timedelta(weeks=1)).date().isoformat()

        return None


# -----------------------------
# Core Extraction Function
# -----------------------------
def extract_tasks(prompt: str) -> ExtractedData:
    """
    Extract tasks using Groq LLaMA model.
    Applies sentiment → priority logic and enforces MAX_TASKS.
    """

    # -------------------------
    # Guardrails
    # -------------------------
    flags = check_guardrails(prompt)
    if flags.sensitive:
        logger.info("Sensitive content detected — anonymizing")
        prompt += " [REDACTED SENSITIVE CONTENT]"

    # -------------------------
    # System Prompt
    # -------------------------
    system_prompt = f"""
You are a task-extraction assistant. Given a voice note, output ONLY valid JSON in this structure:

{{
  "summary": "one-line summary",
  "tasks": [
    {{"name": "task text", "due": null, "assignee": null}}
  ],
  "insights": "short motivational insight"
}}

Rules:
- Extract **maximum {MAX_TASKS} actionable tasks**
- Parse fuzzy dates (tomorrow, EOD, next Monday) into ISO 8601 if possible
- If no clear tasks exist, create one reflective task
- Summary < 50 words
Output JSON only — no commentary.
"""

    # -------------------------
    # Groq API Call
    # -------------------------
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.15,
        max_tokens=400
    )

    # Extract message content (Groq SDK has 2 formats)
    raw = None
    try:
        raw = response.choices[0].message["content"]
    except Exception:
        try:
            raw = response.choices[0].message.content
        except Exception:
            raw = str(response)

    raw = (raw or "").strip()

    # Strip ```json fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    data = json.loads(raw)

    # -------------------------
    # Sentiment Analysis
    # -------------------------
    sentiment = TextBlob(prompt).sentiment.polarity

    for t in data.get("tasks", []):
        # priority + vibe
        if sentiment < 0:
            t["prio"] = "high"
            t["vibe"] = "stressed"
        elif sentiment > 0.2:
            t["prio"] = "low"
            t["vibe"] = "pumped"
        else:
            t["prio"] = "medium"
            t["vibe"] = "neutral"

        # parse fuzzy dates
        if t.get("due"):
            t["due"] = parse_fuzzy_date(t["due"])

        # ensure fields exist
        t.setdefault("assignee", None)

    # -------------------------
    # Enforce MAX_TASKS rule
    # -------------------------
    if "tasks" in data:
        data["tasks"] = data["tasks"][:MAX_TASKS]

    # Ensure insights exists
    if not data.get("insights"):
        data["insights"] = "Keep going — steady progress works."

    # Return validated Pydantic object
    return ExtractedData(**data)

