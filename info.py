from os import environ, getenv
from Script import script

# 🚀 __Bot Configuration__
SESSION = environ.get('SESSION', 'ProBotz')  # Session name
API_ID = int(environ.get('API_ID', ''))
API_HASH = environ.get('API_HASH', '')
BOT_TOKEN = environ.get('BOT_TOKEN', '')

# 👑 __Owner & Admins__
ADMINS = [int(i) for i in environ.get('ADMINS', '7413682152').split()]
AUTH_CHANNEL = [int(i) for i in environ.get("AUTH_CHANNEL", "-1002269651634").split()]
OWNER_USERNAME = environ.get("OWNER_USERNAME", 'SatyajeetKumarOfficial')
BOT_USERNAME = environ.get("BOT_USERNAME", 'QuickFile2LinkProBot')

# 🔗 __Channel & Support Links__
CHANNEL = environ.get('CHANNEL', 'https://t.me/ProBotXUpdate')
SUPPORT = environ.get('SUPPORT', 'https://t.me/ProBotUpdate')
HOW_TO_VERIFY = environ.get('HOW_TO_VERIFY', 'https://t.me/ProBotUpdate')
HOW_TO_OPEN = environ.get('HOW_TO_OPEN', 'https://t.me/ProBotUpdate')

# 📢 __Log Channels__
BIN_CHANNEL = int(environ.get("BIN_CHANNEL", ''))
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", '-'))
PREMIUM_LOGS = int(environ.get("PREMIUM_LOGS", ''))
VERIFIED_LOG = int(environ.get('VERIFIED_LOG', ''))
SUPPORT_GROUP = int(environ.get("SUPPORT_GROUP", ""))

# ✅ __Feature Toggles__
VERIFY = False  # Enable user verification
FSUB = environ.get("FSUB", True)  # Force Subscribe
ENABLE_LIMIT = environ.get("ENABLE_LIMIT", True)
BATCH_VERIFY = False
IS_SHORTLINK = False
MAINTENANCE_MODE = environ.get("MAINTENANCE_MODE", False)
PROTECT_CONTENT = environ.get('PROTECT_CONTENT', False)
PUBLIC_FILE_STORE = environ.get('PUBLIC_FILE_STORE', True)
BATCH_PROTECT_CONTENT = environ.get('BATCH_PROTECT_CONTENT', False)

# 🔗 __Shortlink Configuration__
SHORTLINK_URL = environ.get('SHORTLINK_URL', '')
SHORTLINK_API = environ.get('SHORTLINK_API', '')

# 💾 __Database Configuration__
DB_URL = environ.get('DATABASE_URI', "")
DB_NAME = environ.get('DATABASE_NAME', "ProBotz")

# 📸 __Media & Images__
QR_CODE = environ.get('QR_CODE', 'https://ibb.co/h1DVpLfR')
VERIFY_IMG = environ.get("VERIFY_IMG", "https://ibb.co/h1DVpLfR")
AUTH_PICS = environ.get('AUTH_PICS', 'https://ibb.co/h1DVpLfR')
PICS = environ.get('PICS', 'https://ibb.co/h1DVpLfR')
FILE_PIC = environ.get('FILE_PIC', 'https://ibb.co/h1DVpLfR')

# 📝 __Captions__
FILE_CAPTION = environ.get('FILE_CAPTION', script.CAPTION)
BATCH_FILE_CAPTION = environ.get('BATCH_FILE_CAPTION', script.CAPTION)
CHANNEL_FILE_CAPTION = environ.get('CHANNEL_FILE_CAPTION', script.CAPTION)

# ⏱️ __Time & Limits__
PING_INTERVAL = int(environ.get("PING_INTERVAL", 1200))
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', 60))
RATE_LIMIT_TIMEOUT = int(environ.get("RATE_LIMIT_TIMEOUT", 600))
MAX_FILES = int(environ.get("MAX_FILES", 50))
VERIFY_EXPIRE = int(environ.get('VERIFY_EXPIRE', 90))  # Hours

# ⚙️ __Worker & App Config__
WORKERS = int(environ.get('WORKERS', 10))
MULTI_CLIENT = False
NAME = environ.get('name', 'ProBotz')

# 🌐 __Web Server__
ON_HEROKU = 'DYNO' in environ
APP_NAME = environ.get('APP_NAME') if ON_HEROKU else None

PORT = int(environ.get('PORT', 8080))
NO_PORT = str(environ.get("NO_PORT", "true")).lower() in ("true", "1", "yes")
HAS_SSL = str(environ.get("HAS_SSL", "true")).lower() in ("true", "1", "yes")

# URL Generation
BIND_ADDRESS = environ.get("WEB_SERVER_BIND_ADDRESS", "")   ##without https:// paste the base url here 
FQDN = environ.get("FQDN", BIND_ADDRESS)

if not FQDN.startswith("http"):
    PROTOCOL = "https" if HAS_SSL else "http"
    PORT_SEGMENT = "" if NO_PORT else f":{PORT}"
    
    # Clean up trailing slashes for consistency
    FQDN = FQDN.rstrip('/')
    URL = f"{PROTOCOL}://{FQDN}{PORT_SEGMENT}/"
else:
    URL = FQDN

