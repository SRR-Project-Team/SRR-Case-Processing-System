import os

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