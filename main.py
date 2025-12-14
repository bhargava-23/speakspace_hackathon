import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import logging

from utils import extraction, notion_builder, trends

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice to Notion API",
    version="2.0.0",
    description="SpeakSpace Hackathon – Sentiment-aware voice → Notion automation with WOW Factors."
)

class Payload(BaseModel):
    prompt: str
    note_id: str
    timestamp: str
    speakspace_user_id: str | None = None    # NEW (optional)

async def verify_token(authorization: str = Header(None)):
    expected = f"Bearer {os.getenv('BEARER_TOKEN', 'myhacktoken123')}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return True

@app.get("/")
async def root():
    return {"status": "online", "message": "Voice-to-Notion API running."}

@app.get("/health")
async def health():
    """Verify all components are correctly configured."""
    writable = True
    try:
        with open("data/health_test.tmp", "w") as f:
            f.write("ok")
        os.remove("data/health_test.tmp")
    except:
        writable = False

    return {
        "groq_key_loaded": bool(os.getenv("GROQ_API_KEY")),
        "notion_token_loaded": bool(os.getenv("NOTION_TOKEN")),
        "database_id_loaded": bool(os.getenv("NOTION_DATABASE_ID")),
        "trends_file_write_access": writable,
        "version": "2.0.0"
    }

@app.post("/process")
async def process_voice(payload: Payload, auth=Depends(verify_token)):
    try:
        logger.info(f"Processing note_id={payload.note_id}")

        # 1 — Extraction
        extracted = extraction.extract_tasks(payload.prompt)

        # 2 — Log trends + idempotency handled here
        if trends.note_exists(payload.note_id):
            logger.info("Idempotency triggered — returning existing Notion page URL.")
            existing = trends.get_existing_page(payload.note_id)
            return {"status": "success", "message": "Duplicate note ignored", "page_url": existing}

        trends.log_trend(
            note_id=payload.note_id,
            extracted=extracted.model_dump(),
            timestamp=payload.timestamp,
            user_id=payload.speakspace_user_id
        )

        # 3 — Build Notion Page with audit trail + retry wrapper
        page_url = notion_builder.create_page(
            extracted.model_dump(),
            note_id=payload.note_id,
            timestamp=payload.timestamp,
            user_id=payload.speakspace_user_id
        )

        # Store mapping (idempotency)
        trends.save_page_reference(payload.note_id, page_url)

        return {"status": "success", "message": "Workflow executed", "page_url": page_url}

    except Exception as e:
        logger.exception("Workflow failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
