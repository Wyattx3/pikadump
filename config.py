"""
Configuration settings for Telegram Card Extractor
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API Credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# Session file name
SESSION_NAME = "telegram_card_extractor"

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Output file names
CSV_FILE = OUTPUT_DIR / "cards.csv"
JSON_FILE = OUTPUT_DIR / "cards.json"
TXT_FILE = OUTPUT_DIR / "cards.txt"

# Card type filters (empty list = all types)
ALLOWED_CARD_TYPES = []  # ['Visa', 'Mastercard', 'American Express', 'JCB', 'Discover']

# Monitoring settings
MONITORING_ENABLED = True
CHECK_INTERVAL = 1  # seconds (for future use)

# Logging settings
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "card_extractor.log"
