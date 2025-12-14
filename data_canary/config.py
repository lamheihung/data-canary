import os

# --- Configuration Settings ---

# Read GEMINI_MODEL_NAME from environment variable, default to the stable 2.5-flash
# The user must set this in their environment, e.g., export GEMINI_MODEL_NAME="gemini-2.5-flash"
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# The API key is read directly by the SDK, but we check for its existence here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")