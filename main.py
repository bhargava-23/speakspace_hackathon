import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Local imports
from utils import extraction, notion_builder, trends

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Voice to Notion API",
    version="2.0.0",
    description="SpeakSpace Hackathon – Sentiment-aware voice → Notion automation with WOW Factors."
)


# -------------------------
# Request Schema
# -------------------------
class Payload(BaseModel):
    prompt: str
    note_id: str
    timestamp: str
    speakspace_user_id: str | None = None   # optional audit metadata


# -------------------------
# Bearer Token Auth
# -------------------------
async def verify_token(authorization: str = Header(None)):
    expected = f"Bearer {os.getenv('BEARER_TOKEN', 'myhacktoken123')}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return True


# -------------------------
# Root Route
# -------------------------
@app.get("/")
async def root():
    return {"status": "online", "message": "Voice-to-Notion API running."}


# -------------------------
# Health Check
# -------------------------
@app.get("/health")
async def health():
    writable = True
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/health_test.tmp", "w") as f:
            f.write("ok")
        os.remove("data/health_test.tmp")
    except Exception:
        writable = False

    return {
        "groq_key_loaded": bool(os.getenv("GROQ_API_KEY")),
        "notion_token_loaded": bool(os.getenv("NOTION_TOKEN")),
        "database_id_loaded": bool(os.getenv("NOTION_DATABASE_ID")),
        "trends_file_write_access": writable,
        "version": "2.0.0"
    }


# -------------------------
# Main Workflow Endpoint
# -------------------------
@app.post("/process")
async def process_voice(payload: Payload, auth=Depends(verify_token)):
    try:
        logger.info(f"Processing note_id={payload.note_id}")

        # -----------------------------
        # 1 — Extraction
        # -----------------------------
        extracted = extraction.extract_tasks(payload.prompt)

        # -----------------------------
        # 2 — Idempotency Check
        # -----------------------------
        if trends.note_exists(payload.note_id):
            logger.info("Idempotency triggered — duplicate note ignored.")
            existing_url = trends.get_existing_page(payload.note_id)
            return {
                "status": "success",
                "message": "Duplicate note ignored",
                "page_url": existing_url
            }

        # Log behavioral trends
        trends.log_trend(
            note_id=payload.note_id,
            extracted=extracted.model_dump(),
            timestamp=payload.timestamp,
            user_id=payload.speakspace_user_id
        )

        # -----------------------------
        # 3 — Build Notion Page (with retry logic inside notion_builder)
        # -----------------------------
        page_url = notion_builder.create_page(
            extracted.model_dump(),
            note_id=payload.note_id,
            timestamp=payload.timestamp,
            user_id=payload.speakspace_user_id
        )

        # Store idempotency reference
        trends.save_page_reference(payload.note_id, page_url)

        # -----------------------------
        # Successful Response
        # -----------------------------
        return {
            "status": "success",
            "message": "Workflow executed",
            "page_url": page_url
        }

    except Exception as e:
        logger.exception("Workflow failed")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Run Local Dev Server
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

