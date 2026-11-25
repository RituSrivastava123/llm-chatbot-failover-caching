import os
from typing import List
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

class Settings:
    LLM_API_KEYS_RAW: str = os.getenv("LLM_API_KEYS", "dummy_key_1,dummy_key_2")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "*")
    ENABLE_FAILURE_SIMULATION: bool = os.getenv("ENABLE_FAILURE_SIMULATION", "true").lower() in ("true", "1", "yes")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini/gemini-2.0-flash")
    DEFAULT_SYSTEM_PROMPT: str = os.getenv("DEFAULT_SYSTEM_PROMPT", "You are a helpful and concise AI assistant.")
    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "local")  # "local" (in-memory) or "disk"

    @property
    def key_pool(self) -> List[tuple[str, str]]:
        """
        Parses LLM_API_KEYS into key_1, key_2, ... tuples.
        """
        keys = [k.strip() for k in self.LLM_API_KEYS_RAW.split(",") if k.strip()]
        if not keys:
            keys = ["dummy_key_1", "dummy_key_2"]
        return [(f"key_{i+1}", key) for i, key in enumerate(keys)]

    @property
    def allowed_origins(self) -> List[str]:
        origins = [o.strip() for o in self.ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
        return origins if origins else ["*"]

settings = Settings()
