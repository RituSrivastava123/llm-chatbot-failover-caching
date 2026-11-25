import os
import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test_app.db"
os.environ["LLM_API_KEYS"] = "dummy_key_1,dummy_key_2"
os.environ["ENABLE_FAILURE_SIMULATION"] = "true"
os.environ["CACHE_TYPE"] = "local"

from app.main import app
from app.database import init_db, get_db_path
import litellm
from litellm.caching.caching import Cache

@pytest.fixture(autouse=True)
def clean_db_and_cache():
    # Remove test db if exists
    db_file = get_db_path()
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
    # Initialize fresh db schema
    init_db()
    # Reset LiteLLM cache
    litellm.cache = Cache(type="local")
    yield
    # Cleanup after test
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
