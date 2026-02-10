"""Configuration — loads .env and exposes settings."""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:8003/sse")

if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY is not set. Add it to your .env file.")
