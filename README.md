# Voice to Notion – Sentiment-Aware Task Automation

### SpeakSpace Annual Hackathon 2025 – Final Submission

### Team: Deadly Duo



---

## 1. Problem Statement

Voice notes are one of the fastest ways to capture ideas, but they are also one of the least structured. Users often end up with:

* Unorganized voice memos
* No clear action items
* No prioritization
* No follow-through

Traditional transcription tools only convert speech to text. They do not extract tasks, infer deadlines, or understand urgency.

---

## 2. Solution Overview

**Voice to Notion** is a backend system that processes voice notes from SpeakSpace, analyzes their emotional context, extracts specific action items, and automatically creates a structured Notion page.

Key innovations include:

### • AI-Based Task Extraction

Uses Groq (Llama-3.3-70B) to extract 3–5 tasks, summaries, and insights.

### • Sentiment-Driven Prioritization

The emotional tone influences urgency:

* Negative tone → High priority
* Positive tone → Low priority
* Neutral tone → Medium priority

### • Automated Notion Page Creation

The system generates a Notion page with:

* To-do tasks
* Parsed deadlines
* Insights informed by sentiment
* A pattern analysis section based on historical entries

### • Pattern Tracking

Logs each processed note locally to identify long-term patterns such as stress frequency and workload trends.

---

## 3. Architecture

```
SpeakSpace App
     |
     | (prompt, note_id, timestamp)
     ↓
POST /process (FastAPI Backend)
     |
     |-- AI Task Extraction (Groq)
     |-- Sentiment Scoring (TextBlob)
     |-- Priority + Vibe Assignment
     |-- Trend Logging (local JSON)
     ↓
Notion API – Page Creation
```

---

## 4. Features

* Extracts tasks, deadlines, and assignees
* Assigns priority levels using sentiment analysis
* Creates structured Notion pages
* Adds long-term insights based on historical logs
* Privacy guardrails for sensitive content
* Secured with bearer token authentication

---

## 5. Tech Stack

| Component            | Technology               |
| -------------------- | ------------------------ |
| AI Model             | Groq – Llama-3.3-70B     |
| API Framework        | FastAPI                  |
| Sentiment Analysis   | TextBlob                 |
| Integration          | Notion API               |
| Deployment           | Railway                  |
| Validation & Logging | Pydantic, Python Logging |

---

## 6. API Usage

### Endpoint

```
POST /process
```

### Headers

```
Authorization: Bearer <your_token>
Content-Type: application/json
```

### Request Body

```json
{
  "prompt": "Finish the project by tomorrow, feeling stressed about the deadline",
  "note_id": "12345",
  "timestamp": "2025-12-12T10:00:00Z"
}
```

### Response

```json
{
  "status": "success",
  "message": "Workflow executed"
}
```

---

## 7. SpeakSpace Integration

### Steps:

1. Deploy backend on Railway
2. Copy production URL (e.g., `https://yourapp.up.railway.app/process`)
3. Open SpeakSpace → Workflow Module → Custom Actions → Add New
4. Fill in:

   * API URL → your deployed `/process`
   * Authorization → Bearer
   * Token → same as `BEARER_TOKEN` in `.env`
   * Prompt Template:

     ```
     {"prompt": "$PROMPT", "note_id": "$NOTE_ID", "timestamp": "$TIMESTAMP"}
     ```
   * Notes Selector: Single Note

SpeakSpace will automatically send all required data.

---

## 8. Environment Variables

```
GROQ_API_KEY=your_key_here
NOTION_TOKEN=your_notion_secret
NOTION_DATABASE_ID=your_database_id
BEARER_TOKEN=myhacktoken123
MAX_TASKS=5
```

---

## 9. Running Locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Server runs at:

```
http://localhost:8000
```

Interactive documentation:

```
http://localhost:8000/docs
```

---

## 10. Deployment (Railway)

1. Push project to GitHub
2. Create new Railway project → Deploy from GitHub
3. Add environment variables
4. Railway will run:

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

5. Use the public URL in SpeakSpace.

---

## 11. Why This Project Stands Out

* Converts emotional, unstructured voice notes into structured task plans
* Introduces sentiment-aware prioritization not commonly seen in productivity tools
* Provides complete automation between SpeakSpace, backend, AI extraction, and Notion
* Fast, reliable, and designed for real-world scalability
* Clear, maintainable architecture suitable for production

---

## 12. Folder Structure

```
voice-to-notion/
│
├── main.py
├── utils/
│   ├── extraction.py
│   ├── notion_builder.py
│   ├── validators.py
│   ├── trends.py
│
├── data/trends.json
├── deployment/
├── demo/
├── requirements.txt
└── README.md
```

---

## 13. Conclusion

This project demonstrates how voice input, emotional intelligence, and automation can work together to streamline productivity. The system produces structured Notion pages from natural voice notes while understanding the user's tone and urgency, offering meaningful value beyond simple transcription.
