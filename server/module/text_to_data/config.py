from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).parent.parent.parent / ".server.env"
load_dotenv(dotenv_path=env_path)


# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama | openai | anthropic | google
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Database for SQL execution
SQL_DATABASE_URL = os.getenv("SQL_DATABASE_URL", os.getenv("DATABASE_URL", ""))

# Agent memory
AGENT_MEMORY_MAX_ITEMS = int(os.getenv("AGENT_MEMORY_MAX_ITEMS", "1000"))

# Vanna UI config
VANNA_DEV_MODE = os.getenv("VANNA_DEV_MODE", "false").lower() == "true"
