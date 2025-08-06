import os
from typing import Dict

# Load environment variables with fallbacks
def load_env_with_fallback():
    """Load environment variables with fallback values."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # If python-dotenv is not available, just use os.getenv
        pass

load_env_with_fallback()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_ENABLE_CATEGORIZATION = os.getenv("OPENAI_ENABLE_CATEGORIZATION", "false").lower() == "true"

# Default settings for missing environment variables
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./finance_bot.db"

if not TELEGRAM_TOKEN:
    print("⚠️  WARNING: TELEGRAM_TOKEN not set. Bot will not function without it.")

# Chart and cache configuration
CHART_CACHE_DIR = os.getenv("CHART_CACHE_DIR", "cache/chart_cache")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# Financial analysis settings
DEFAULT_ANALYSIS_DAYS = int(os.getenv("DEFAULT_ANALYSIS_DAYS", "90"))
MAX_BUDGET_CATEGORIES = int(os.getenv("MAX_BUDGET_CATEGORIES", "20"))
MAX_FINANCIAL_GOALS = int(os.getenv("MAX_FINANCIAL_GOALS", "10"))

# Create directories if they don't exist
try:
    os.makedirs(CHART_CACHE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")

# App configuration
APP_CONFIG = {
    'max_file_size_mb': int(os.getenv("MAX_FILE_SIZE_MB", "10")),
    'session_timeout_hours': int(os.getenv("SESSION_TIMEOUT_HOURS", "24")),
    'enable_debug_logging': os.getenv("ENABLE_DEBUG_LOGGING", "False").lower() == "true",
    'chart_quality': os.getenv("CHART_QUALITY", "high"),  # low, medium, high
    'default_currency': os.getenv("DEFAULT_CURRENCY", "IDR"),
}
