import os

# --- Configuration Settings ---

# For OpenAI and OpenAI-compatible API (e.g. Moonshot AI)
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "kimi-k2-thinking")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.moonshot.ai/v1")
