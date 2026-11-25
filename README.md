# Lyftr AI Full-Stack Assignment: Resilient LLM Chatbot

> A resilient, production-grade LLM Chatbot web application featuring multi-key automatic failover, response caching via LiteLLM, multi-turn state persistence in SQLite, per-request token usage tracking, and a failure simulation test hook.

---

## 1. Live URLs

- **Frontend Application:** `https://llm-chatbot-failover-caching.vercel.app` *(Pending Vercel deployment)*
- **Backend API Base URL:** `https://llm-chatbot-backend-py4h.onrender.com`
- **Health Check Endpoint:** `https://llm-chatbot-backend-py4h.onrender.com/health`
- **GitHub Repository:** `https://github.com/RituSrivastava123/llm-chatbot-failover-caching`
- **Demo Video (2–3 mins):** `https://loom.com/share/...` *(Pending recording)*

---

## 2. Run Locally: With Docker and Without

### Option A: With Docker (Recommended)

Ensure Docker and Docker Compose are installed, then run:

```bash
# 1. Clone repository
git clone https://github.com/your-username/llm-chatbot-failover-caching.git
cd llm-chatbot-failover-caching

# 2. Configure environment variables
cp .env.example .env
# Edit .env and supply your LLM keys (e.g. Gemini, Groq, or OpenAI keys)

# 3. Start the full stack with make
make up
```

Once running:
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

To view logs or stop:
```bash
make logs   # Stream logs
make down   # Stop and clean up containers
```

---

### Option B: Without Docker (Local Development)

#### 1. Backend Setup (FastAPI + LiteLLM + SQLite)
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite
pytest -v

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup (React + Vite + Tailwind CSS)
```bash
cd frontend

# Install Node packages
npm install

# Start Vite dev server on port 3000
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 3. Design Decisions: Key Fallback, Caching, SQLite Session Storage

### Key Fallback Architecture & Auto-Failover
- **Key Pool Orchestration:** Configured with `LLM_API_KEYS` containing comma-separated keys (`key_1`, `key_2`, ...). Key IDs are tracked transparently, ensuring the raw API keys are never exposed in responses or logs.
- **Failover Logic:** When an LLM invocation encounters rate limiting (HTTP 429), quota exhaustion, or server errors (500, 502, 503), the gateway catches the exception, increments `fallback_attempts`, and automatically retries the request using the subsequent key in the pool.
- **Graceful Exhaustion:** If all keys in the pool fail, the backend returns a clean HTTP 503 JSON response `{"detail": "all providers unavailable"}` without unhandled exceptions or stack traces.
- **Failure Simulation (`X-Simulate-Failure`):** Supports header formats like `key_1=429`, `key_1=429,key_2=500`, and `*=429`. Honored exclusively when `ENABLE_FAILURE_SIMULATION=true`, enabling realistic failover demonstration without burning live API quotas.

### LiteLLM Response Caching
- **Deterministic Cache Key:** Built as a hash of the target `model` and the full message sequence sent to the LLM (`[system_prompt, ...history, new_message]`).
- **Hit Detection & Performance:** If an identical message sequence has already been resolved, LiteLLM's cache immediately returns the stored completion and token metrics with `resolution_source: "LLM_CACHE"`, `key_id: null`, `fallback_attempts: 0`, and sub-millisecond to low millisecond latency.
- **Cross-Session Consistency:** Sending the same first prompt in two distinct sessions produces a cache hit on the second invocation while keeping session histories strictly isolated.

### SQLite Session Storage
- **Zero External Dependencies:** Built strictly on SQLite (no Redis or PostgreSQL), maintaining state across server restarts using a persistent volume mounted at `/data`.
- **Atomic Persistence:** User messages and assistant replies are committed atomically in a single transaction. Failed requests (HTTP 422 or 503) are never written to history.
- **WAL Mode & Thread Safety:** Utilizes SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) with connection timeouts to ensure high concurrent read/write throughput without database locking errors.

---

## 4. Verification: How to See Failover, Cache Hits and Per-Message Token Usage

### 1. Verification of Caching Accuracy
Send the exact same initial query in two separate sessions:

**Session 1 (First query - LIVE_INFERENCE):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sess-alpha", "message": "What is the capital of France?"}'
```
*Response contains:*
```json
"metadata": {
  "resolution_source": "LIVE_INFERENCE",
  "key_id": "key_1",
  "fallback_attempts": 0,
  "latency_ms": 750
}
```

**Session 2 (Same query in new session - LLM_CACHE):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sess-beta", "message": "What is the capital of France?"}'
```
*Response contains:*
```json
"metadata": {
  "resolution_source": "LLM_CACHE",
  "key_id": null,
  "fallback_attempts": 0,
  "latency_ms": 2
}
```
*Notice: Identical answer, `LLM_CACHE` source, null `key_id`, zero fallback attempts, and substantially lower latency.*

---

### 2. Verification of Automatic Key Failover
Simulate `key_1` returning an HTTP 429 quota/rate error:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: key_1=429" \
  -d '{"session_id": "sess-failover", "message": "Explain key failover."}'
```
*Response:*
```json
"metadata": {
  "resolution_source": "LIVE_INFERENCE",
  "key_id": "key_2",
  "fallback_attempts": 1
}
```
*The request succeeds with 200 OK answered by `key_2` after 1 fallback attempt.*

---

### 3. Verification of All Providers Unavailable (Clean 503)
Simulate all keys failing:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: *=429" \
  -d '{"session_id": "sess-allfail", "message": "Will fail"}'
```
*Status: `503 Service Unavailable`*
*Body:*
```json
{"detail": "all providers unavailable"}
```
*Verifying history isolation:*
```bash
curl http://localhost:8000/sessions/sess-allfail/messages
```
*Returns `404 {"detail": "session not found"}` confirming failed requests are never added to SQLite history.*

---

### 4. Verification of Per-Message Token Usage
- In the UI, each assistant bubble shows `In: <input_tokens>` and `Out: <output_tokens>` for that request only.
- Two equal-length first messages in separate sessions report identical/equivalent input tokens, confirming usage is per-request rather than an accumulating conversation total.

---

## 5. Setup Used: Editor and AI Tools

- **Primary Editor:** Visual Studio Code & Antigravity IDE
- **Runtimes & Frameworks:** Python 3.12 (FastAPI, Uvicorn, LiteLLM, Pydantic v2, Pytest), Node.js v24 (React 18, Vite 6, Tailwind CSS)
- **Containerization:** Docker Engine, Docker Compose, Multi-stage alpine/slim images
- **AI Tools & Assistants:** Antigravity (Google DeepMind) for end-to-end scaffolding, test suite generation, and API contract compliance checking.

---

## 6. Bonus Features (If Any): What We Added Beyond Requirements and Why

1. **Interactive In-UI Failure Simulator Bar:** Added toggle buttons (`None`, `key_1=429`, `key_1=500`, `*=429`) directly in the web header. This enables recruiters and evaluators to test failover live in the browser without manually crafting curl commands.
2. **Dynamic Live Health Dashboard:** Header displays real-time connectivity status to `/health`, showing configured key count and cache status with an indicator pill.
3. **Session Reset ("New Chat") Control:** Instant client-side session generation and history reset without full page reload.
4. **Configurable System Prompt Drawer:** Expandable UI bar with `data-testid="system-prompt-input"` allowing dynamic session system prompts.
5. **Modern Dark-Mode UI with Semantic Visual Badges:** Emerald badge for `LLM_CACHE`, Indigo badge for `LIVE_INFERENCE`, and amber warnings for failover attempts.
6. **Graceful In-Chat Error Cards:** User-friendly error banners in the chat feed for 422 or 503 errors preventing any white-screen-of-death or silent failure.

---

## API Contract Summary

| Endpoint | Method | Description | Success Response |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Health status, keys loaded, cache status | `200 {"status":"ok","keys_configured":2,"cache_enabled":true}` |
| `/chat` | `POST` | Sends chat message with failover & cache | `200 {"session_id":"...","reply":"...","metadata":{...}}` |
| `/sessions/{id}/messages` | `GET` | Retrieves full session history from SQLite | `200 {"session_id":"...","messages": [...]}` |

---

## License
MIT License. Created for the Lyftr AI Full-Stack Assessment.
