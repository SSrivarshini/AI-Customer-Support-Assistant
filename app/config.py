import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

# Env vars forwarded to the MCP server subprocesses
MCP_ENV_KEYS = [
    "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME",
    "GOOGLE_SERVICE_ACCOUNT_FILE", "GOOGLE_CALENDAR_ID", "TIMEZONE",
]
