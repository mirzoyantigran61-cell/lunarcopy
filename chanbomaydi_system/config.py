"""
⚙️ Nitro Proxy - Configuration
"""
import os

# Paths relative to this package (do not depend on process CWD — fixes systemd / deleted cwd issues)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")

# Bot Tokens
TOKENS = {
    "owner": "8640728990:AAEbIP1ljEry_AP6c9DWZ2iXYW6oIWT69Ps",
    "admin": "8640728990:AAEbIP1ljEry_AP6c9DWZ2iXYW6oIWT69Ps",
    "user": "8726810917:AAHhhGVzODBCFWnpfvz7MSxTws0YiSAzsm8"
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
SUPPORT_USERNAME = "@erzohack"
MINI_APP_URL = "https://nguyenvantai/miniapp"

# System Name
SYSTEM_NAME = "Uyen Proxy"
