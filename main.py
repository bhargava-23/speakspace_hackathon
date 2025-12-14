from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
import traceback
import os
import json

# --- Import your existing logic ---
from utils.extraction import extract_tasks_from_prompt
from utils.notion_builder import create_notion_page
from utils.trends import log_trends

app = FastAPI(title="Voice to Notion – SpeakSpace")

# -------------------------------
# HEALTH CHECK (used by Render)
# -------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "groq_key_loaded": bool(os.getenv("GROQ_API_KEY")),
        "notion_token_loaded": bool(os.getenv("NOTION_TOKEN")),
        "database_id_loaded": bool(os.getenv("NOTION_DATABASE_ID")),
        "version": "final-hackathon"
    }


# ---------------------------------
# MAIN ENDPOINT (SPEAKSPACE SAFE)
# ---------------------------------
@app.post("/process")
async def process(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    🔥 SPEAKSPACE-SAFE ENDPOINT 🔥

    - Accepts ANY payload
    - No schema
    - No validation errors
    - Never throws 422
    - Always returns 200
    """

    try:
        # 1️⃣ Read raw body safely
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        print("📥 RAW SPEAKSPACE PAYLOAD:")
        print(json.dumps(payload, indent=2))

        # 2️⃣ Extract prompt from ANY possible key
        prompt = (
            payload.get("prompt")
            or payload.get("text")
            or payload.get("note")
            or payload.get("content")
            or payload.get("transcription")
            or payload.get("data")
            or payload.get("message")
            or ""
        )

        # Absolute fallback
        if not prompt:
            prompt = json.dumps(payload)

        print("🧠 EXTRACTED PROMPT:")
        print(prompt)

        # 3️⃣ Run extraction (NO hard failure)
        try:
            extracted = extract_tasks_from_prompt(prompt)
        except Exception as e:
            print("⚠️ Extraction failed:", str(e))
            extracted = {
                "tasks": [],
                "sentiment": "unknown",
                "summary": prompt
            }

        # 4️⃣ Create Notion page (safe)
        try:
            page_url = create_notion_page(
                extracted_data=extracted,
                raw_prompt=prompt
            )
        except Exception as e:
            print("⚠️ Notion creation failed:", str(e))
            page_url = None

        # 5️⃣ Log trends (non-blocking)
        try:
            log_trends(extracted)
        except Exception as e:
            print("⚠️ Trend logging failed:", str(e))

        # 6️⃣ ALWAYS return success (NO 422 EVER)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "SpeakSpace request processed",
                "page_url": page_url,
                "received_keys": list(payload.keys())
            }
        )

    except Exception as e:
        # 🚨 ABSOLUTE FAILSAFE (never break SpeakSpace)
        print("🔥 FATAL ERROR:")
        traceback.print_exc()

        return JSONResponse(
            status_code=200,
            content={
                "status": "accepted",
                "message": "Request received but partially processed",
                "error": str(e)
            }
        )
