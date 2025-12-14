import os
import json
import logging
from dotenv import load_dotenv
from groq import Groq
from textblob import TextBlob
from dateutil import parser as date_parser
from datetime import datetime, timedelta

from .validators import ExtractedData, check_guardrails

load_dotenv()
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_fuzzy_date(date_str: str) -> str | None:
    if not date_str:
        return None
    try:
        parsed = date_parser.parse(date_str, fuzzy=True)
        return parsed.date().isoformat()
    except Exception:
        ds = date_str.lower()
        today = datetime.now()
        if "tomorrow" in ds:
            return (today + timedelta(days=1)).date().isoformat()
        if "eod" in ds or "end of day" in ds:
            return today.date().isoformat()
        if "next week" in ds:
            return (today + timedelta(weeks=1)).date().isoformat()
        return None

def extract_tasks(prompt: str) -> ExtractedData:
    """
    Uses Groq (LLaMA model) to extract tasks; assigns priority based on sentiment.
    Returns a validated ExtractedData instance.
    """
    # Guardrails
    flags = check_guardrails(prompt)
    if flags.sensitive:
        logger.info("Sensitive content - redacted for extraction")
        prompt = prompt + " [REDACTED SENSITIVE CONTENT]"

    system_prompt = """
You are a task-extraction assistant. Given a voice note, output ONLY valid JSON
in this EXACT structure:

{
  "summary": "one-line summary",
  "tasks": [
    {"name": "task text", "due": null, "assignee": null}
  ],
  "insights": "short motivational insight"
}

Rules:
- Extract maximum 3-5 actionable tasks
- Parse fuzzy dates (tomorrow, EOD, next Monday) into ISO format if possible
- If no clear tasks exist, create a single reflective task
- Keep summary < 50 words
Return compact JSON only.
"""

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.18,
        max_tokens=400
    )

    # Groq response: robust parsing
    raw = None
    try:
        # Try both attribute access styles to be robust to SDK versions
        raw = response.choices[0].message["content"]
    except Exception:
        try:
            raw = response.choices[0].message.content
        except Exception:
            raw = str(response)
    raw = (raw or "").strip()
    # strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1].strip()
        if raw.startswith("json"):
            raw = raw[len("json"):].strip()
    # parse JSON
    data = json.loads(raw)

    # sentiment
    sentiment = TextBlob(prompt).sentiment.polarity
    # assign prio/vibe and normalize dates
    for t in data.get("tasks", []):
        if sentiment < 0:
            t["prio"] = "high"
            t["vibe"] = "stressed"
        elif sentiment > 0.2:
            t["prio"] = "low"
            t["vibe"] = "pumped"
        else:
            t["prio"] = "medium"
            t["vibe"] = "neutral"

        if t.get("due"):
            t["due"] = parse_fuzzy_date(t["due"])

        # ensure fields exist
        if "assignee" not in t:
            t["assignee"] = None

    # ensure insights and summary exist
    if not data.get("insights"):
        data["insights"] = "Keep going — small steps win."

    # Validate and return pydantic model (raises ValueError on invalid)
    return ExtractedData(**data)
