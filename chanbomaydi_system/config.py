"""
⚙️ Tigran Proxy - Configuration
"""
import os

# Paths relative to this package (do not depend on process CWD — fixes systemd / deleted cwd issues)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")

# Bot Tokens
TOKENS = {
    "owner": "8854847237:AAFyrA7wHIg6RjqRbggud2B-PMImGVmzNws",
    "admin": "8865666603:AAHJ7Yjn7XXBFOohybPJmXZulR76jC8QzQE",
    "user": "8951026225:AAH89YWLZe0XVBE-3e5PlKTGLFFkPbhBBrM"
}

# Owner ID
OWNER_ID =5855012627  # Replace with your Telegram user ID (integer)

# Pricing (in USD)
PRICING = {
    "day": 1.0,      # $1 per day
    "week": 3.0,     # $3 per week
    "month": 5.0     # $5 per month
}

# Duration in days
DURATIONS = {
    "day": 1,
    "week": 7,
    "month": 30
}

# Files (absolute under nitro_system/data/)
DB_FILE = os.path.join(_DATA_DIR, "database.json")
IPS_FILE = os.path.join(_DATA_DIR, "allowed_ips.json")
KEYS_FILE = os.path.join(_DATA_DIR, "license_keys.json")

# Settings
MAX_KEYS_PER_ADMIN = 1000
IP_API_URL = "https://api.ipify.org?format=json"
# User-facing: public IP lookup (educational; user copies IPv4 manually)
IP_LOOKUP_URL = "https://www.whatismyip.com/"
SUPPORT_USERNAME = "@TigranUser_bot"
MINI_APP_URL = "https://lunarcopy-production.up.railway.app/download/TigranXTest.zip""

# System Name
SYSTEM_NAME = "Uyen Proxy"
