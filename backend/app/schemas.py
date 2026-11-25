from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128, description="Client generated session id")
    message: str = Field(..., description="User message text (1-4000 chars after trimming)")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt override")

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        s = v.strip()
        if not s or len(s) > 128:
            raise ValueError("session_id must be between 1 and 128 characters")
        return s

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("message cannot be empty or whitespace only")
        if len(s) > 4000:
            raise ValueError("message cannot exceed 4000 characters after trimming")
        return s

class ChatMetadata(BaseModel):
    resolution_source: Literal["LIVE_INFERENCE", "LLM_CACHE"]
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    key_id: Optional[str] = None
    fallback_attempts: int

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: ChatMetadata

class HealthResponse(BaseModel):
    status: str
    keys_configured: int
    cache_enabled: bool

class StoredMessage(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

    def model_dump(self, *args, **kwargs):
        kwargs["exclude_none"] = True
        return super().model_dump(*args, **kwargs)

class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[StoredMessage]

class ErrorResponse(BaseModel):
    detail: Any
