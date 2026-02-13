import os
import re
from pathlib import Path

# Auto-load .env file if it exists (before reading environment variables)
# This ensures .env file is loaded even if load_dotenv wasn't called yet
try:
    from dotenv import load_dotenv
    # Try to find .env file in backend directory
    # This file is in backend/config/settings.py, so .env should be in backend/.env
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent  # Go up from config/ to backend/
    env_file = backend_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file, override=True)
except ImportError:
    # python-dotenv not installed, skip
    pass
except Exception:
    # Ignore errors during .env loading
    pass

# LLM API Configuration
# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key

# Proxy Configuration (for regions where OpenAI is blocked)
OPENAI_PROXY_URL = os.getenv("OPENAI_PROXY_URL", "http://127.0.0.1:7890")  # Clash default proxy
OPENAI_USE_PROXY = os.getenv("OPENAI_USE_PROXY", "true").lower() == "true"  # Enable proxy by default

# Default to OpenAI API
LLM_API_KEY = OPENAI_API_KEY
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai"

# SurrealDB Configuration
SURREALDB_URL = "ws://127.0.0.1:8000/rpc"  # SurrealDB本地地址
SURREALDB_NAMESPACE = "tree_case"          # 树木case专属命名空间
SURREALDB_DATABASE = "tree_case_db"        # 树木case专属数据库
SURREALDB_USER = "root"                    # 默认账号
SURREALDB_PASS = "root"                    # 默认密码
# backend directory absolute path
BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
SURREALDB_PERSIST_PATH = str(BACKEND_DIR / "data" / "tree_case_surrealdb")

# Embedding Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")  # "openai" or "ollama"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")  # 推荐的 embedding 模型
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")  # default chat model for Ollama
# Batch size for Ollama /api/embed (input array). Larger = fewer requests; >16 may reduce quality.
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))

# RAG Knowledge Base: max chunks per file (over limit triggers adaptive larger chunk size so full file is indexed)
MAX_RAG_CHUNKS = int(os.getenv("MAX_RAG_CHUNKS", "5000"))

# Server: keep-alive timeout (seconds) so long-running clients/proxies don't get dropped
UVICORN_TIMEOUT_KEEP_ALIVE = int(os.getenv("UVICORN_TIMEOUT_KEEP_ALIVE", "120"))

# Security mode: fail fast on unsafe defaults
SECURE_MODE = os.getenv("SECURE_MODE", "true").lower() == "true"


def _is_weak_jwt_secret(secret: str) -> bool:
    lowered = (secret or "").lower()
    if len(secret or "") < 32:
        return True
    if re.fullmatch(r"[A-Za-z0-9]+", secret or "") and len(secret or "") < 40:
        return True
    weak_markers = ("please-change", "changeme", "default", "secret")
    return any(marker in lowered for marker in weak_markers)


def ensure_security_config() -> None:
    """Validate required security-related settings."""
    if not SECURE_MODE:
        return
    jwt_secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY is required")
    if _is_weak_jwt_secret(jwt_secret):
        raise RuntimeError("JWT_SECRET_KEY is too weak; use at least 32 high-entropy characters")