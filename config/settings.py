import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Default settings for missing environment variables
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./finance_bot.db"

# Chart and cache configuration
CHART_CACHE_DIR = os.getenv("CHART_CACHE_DIR", "cache/chart_cache")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# Financial analysis settings
DEFAULT_ANALYSIS_DAYS = int(os.getenv("DEFAULT_ANALYSIS_DAYS", "90"))
MAX_BUDGET_CATEGORIES = int(os.getenv("MAX_BUDGET_CATEGORIES", "20"))
MAX_FINANCIAL_GOALS = int(os.getenv("MAX_FINANCIAL_GOALS", "10"))

# Create directories if they don't exist
os.makedirs(CHART_CACHE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
