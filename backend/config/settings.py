import os
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
# OpenAI API (currently in use)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key

# Volcengine API (kept for future use, currently disabled)
ARK_API_KEY = os.getenv("ARK_API_KEY")  # Volcengine (Doubao) API key

# Proxy Configuration (for regions where OpenAI is blocked)
OPENAI_PROXY_URL = os.getenv("OPENAI_PROXY_URL", "http://127.0.0.1:7890")  # Clash default proxy
OPENAI_USE_PROXY = os.getenv("OPENAI_USE_PROXY", "true").lower() == "true"  # Enable proxy by default

# Default to OpenAI API
LLM_API_KEY = OPENAI_API_KEY
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "volcengine"