# **Voice-To-Notion: Emotion-Aware Task Automation for SpeakSpace**

### **Team: DEADLY DUO**

A fast, reliable system that transforms raw voice notes into structured, prioritized Notion pages. Designed specifically for the **SpeakSpace Hackathon**, this backend demonstrates emotional intelligence, real-world usability, and strong engineering discipline.

---

# **1. Project Overview**

Voice notes are quick to record—but easy to lose, messy to search, and difficult to turn into action.

Our system fixes this.

### **What it does:**

* Extracts actionable tasks from a voice note
* Understands the user’s emotional tone (stressed / pumped / neutral)
* Assigns priority automatically based on sentiment
* Creates a well-formatted Notion page with tasks, insights, and patterns
* Provides trend analysis across notes
* Ensures reliability with retries, guardrails, and idempotency

This submission focuses on clarity, reliability, and judge-friendly testing.

---

# **2. System Architecture**

```
SpeakSpace → Backend API → Groq LLaMA Extraction → Sentiment Analysis
      → Notion Page Builder → Return page_url
```

### Key Components

* **FastAPI** backend
* **Groq LLaMA-3.x** for high-speed, accurate extraction
* **TextBlob** for sentiment analysis
* **Notion API** for structured task creation
* **Trend logging** for patterns
* **Retry system + guardrails** for reliability

---

# **3. Repository Structure**

```
voice-to-notion/
│
├── main.py                         # FastAPI server
├── requirements.txt
├── README.md
│
├── utils/
│   ├── extraction.py               # Groq + sentiment + task logic
│   ├── notion_builder.py           # Notion formatting + retries
│   ├── trends.py                   # Patterns + idempotency
│   └── validators.py               # Input validation + guardrails
│
├── data/                           # Created automatically at runtime
└── .env.example
```

---

# **4. Quick Setup (5 Minutes)**

### **Install dependencies**

```bash
pip install -r requirements.txt
```

### **Create your `.env` file**

Copy `.env.example` → `.env` and fill:

```
GROQ_API_KEY=your_key_here
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
BEARER_TOKEN=myhacktoken123
MAX_TASKS=5
```

Judges can use their own credentials or our demo instructions.

---

# **5. Running Locally**

```bash
uvicorn main:app --reload
```

Backend will start at:

```
http://localhost:8000
```

---

# **6. API Specification**

## **POST /process** — Main workflow

### **Headers**

```
Authorization: Bearer myhacktoken123
Content-Type: application/json
```

### **Request body**

```json
{
  "prompt": "Finish presentation by tomorrow, feeling stressed",
  "note_id": "abc123",
  "timestamp": "2025-12-10T12:00:00Z",
  "speakspace_user_id": "user001"
}
```

### **Response**

```json
{
  "status": "success",
  "message": "Workflow executed",
  "page_url": "https://www.notion.so/..."
}
```

Judges can click the `page_url` to immediately verify correctness.

---

# **7. Health Check**

## **GET /health**

Returns environment + system readiness:

```json
{
  "groq_key_loaded": true,
  "notion_token_loaded": true,
  "database_id_loaded": true,
  "trends_file_write_access": true,
  "version": "2.0.0"
}
```

This allows judges to validate deployment instantly.

---

# **8. SpeakSpace Action Configuration**

Judges can plug this in directly:

```json
{
  "title": "Voice to Notion Tasks",
  "description": "Convert voice notes into structured Notion action pages with sentiment-based priority.",
  "notes_selector": "single_note",
  "api_url": "https://deadly-duo-voice-notion-api.onrender.com/process",
  "authorization": {
    "type": "bearer",
    "token": "myhacktoken123"
  }
}
```

---

# **9. Deployment Instructions (Render)**

Our backend is deployed on **Render**.

### **How we deployed (for judge transparency):**

1. Pushed GitHub repo
2. Created a new Web Service on Render
3. Added environment variables
4. Render installed dependencies automatically
5. Start command:

   ```
   uvicorn main:app --host 0.0.0.0 --port 10000
   ```
6. Deployment succeeded

### **Live Production URL**

## **[https://deadly-duo-voice-notion-api.onrender.com](https://deadly-duo-voice-notion-api.onrender.com)**

---

# **10. How Judges Can Test the System**

### **Option A: Using SpeakSpace**

1. Add the custom action
2. Record a voice note
3. Select “Voice to Notion Tasks”
4. Open the Notion database
5. A new page appears with:

   * Extracted tasks
   * Priority colors
   * Sentiment-based insights
   * Pattern analysis
   * Audit trail

### **Option B: Using curl or Postman**

```bash
curl -X POST "https://deadly-duo-voice-notion-api.onrender.com/process" \
  -H "Authorization: Bearer myhacktoken123" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Deploy project tomorrow, stressed","note_id":"demo1","timestamp":"2025-12-10T10:00:00Z"}'
```

---

# **11. Why This Project Stands Out**

### **Innovation**

* Emotion-aware task prioritization
* Automatic motivational insight generation
* Pattern intelligence (stress/workload trends)
* Ethical guardrails

### **Execution Quality**

* Clean architecture
* Strong validation
* Idempotent & reliable
* Retry logic for all Notion operations

### **Judge Convenience**

* Ready-to-test API
* Clear endpoints
* Health diagnostics
* Minimal setup

---

# **12. Team**

### **DEADLY DUO**

* Bhargava Krishna G
* Hithesh M

Built with a focus on clarity, reliability, and real-world usability.

---

# **13. Closing Note**

This system demonstrates how voice interfaces can become **intelligent productivity engines** when combined with emotional understanding and structured automation.

Thank you for reviewing our submission.
