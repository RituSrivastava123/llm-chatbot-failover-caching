import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, check_db_health, get_session_messages, save_interaction
from app.gateway import execute_chat_completion, AllProvidersUnavailableException, parse_simulate_failure_header
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SessionHistoryResponse,
    StoredMessage,
    ChatMetadata,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing database schema...")
    init_db()
    yield
    # Shutdown
    logger.info("Application shutting down...")

app = FastAPI(
    title="LLM Chatbot Gateway API",
    lifespan=lifespan,
    docs_url=None,  # Clean API
    redoc_url=None
)

# CORS setup
origins = settings.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers ensuring all errors return {"detail": ...}
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Returns 200 once the app is running, the database is reachable and the key pool is loaded.
    { "status": "ok", "keys_configured": 2, "cache_enabled": true }
    """
    db_ok = check_db_health()
    if not db_ok:
        raise HTTPException(status_code=500, detail="database unreachable")

    keys_count = len(settings.key_pool)
    return HealthResponse(
        status="ok",
        keys_configured=keys_count,
        cache_enabled=True
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    x_simulate_failure: Optional[str] = Header(None, alias="X-Simulate-Failure")
):
    """
    Chat endpoint supporting multi-turn memory, response caching, key failover, and failure simulation.
    """
    # 1. Fetch existing session history from SQLite (oldest first)
    history_messages = get_session_messages(req.session_id) or []

    # 2. Build full message list sent to LLM
    system_prompt = req.system_prompt if req.system_prompt is not None else settings.DEFAULT_SYSTEM_PROMPT
    full_messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        full_messages.append({"role": msg["role"], "content": msg["content"]})
    full_messages.append({"role": "user", "content": req.message})

    # 3. Call LiteLLM gateway with caching and failover
    try:
        reply, metadata_dict = execute_chat_completion(
            messages=full_messages,
            model=settings.DEFAULT_MODEL,
            simulate_header=x_simulate_failure
        )
    except AllProvidersUnavailableException:
        raise HTTPException(status_code=503, detail="all providers unavailable")
    except Exception as e:
        logger.error(f"Error during chat completion: {e}")
        raise HTTPException(status_code=503, detail="all providers unavailable")

    # 4. Save interaction atomically to SQLite only upon success (failed requests never saved)
    assistant_metadata = {
        "resolution_source": metadata_dict["resolution_source"],
        "input_tokens": metadata_dict["input_tokens"],
        "output_tokens": metadata_dict["output_tokens"]
    }
    save_interaction(
        session_id=req.session_id,
        user_content=req.message,
        assistant_content=reply,
        assistant_metadata=assistant_metadata
    )

    metadata = ChatMetadata(**metadata_dict)
    return ChatResponse(
        session_id=req.session_id,
        reply=reply,
        metadata=metadata
    )

@app.get("/sessions/{session_id}/messages")
async def get_session_history(session_id: str):
    """
    Returns the stored history of one session from SQLite, oldest first, without the system prompt.
    Returns 404 {"detail": "session not found"} if session unknown.
    """
    messages = get_session_messages(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="session not found")

    formatted_messages = []
    for m in messages:
        if m["role"] == "assistant":
            formatted_messages.append({
                "role": m["role"],
                "content": m["content"],
                "metadata": m.get("metadata", {})
            })
        else:
            formatted_messages.append({
                "role": m["role"],
                "content": m["content"]
            })

    return {
        "session_id": session_id,
        "messages": formatted_messages
    }
