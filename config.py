import os
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token - should be set in environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Admin user IDs (comma-separated in env var)
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(id_str.strip()) for id_str in admin_ids_str.split(",")]
    except ValueError:
        logger.error("Invalid ADMIN_USER_IDS format. Use comma-separated integers.")

# Default admin ID if no admins are specified
DEFAULT_ADMIN_ID = os.getenv("DEFAULT_ADMIN_ID")
if DEFAULT_ADMIN_ID:
    try:
        DEFAULT_ADMIN_ID = int(DEFAULT_ADMIN_ID)
        if DEFAULT_ADMIN_ID not in ADMIN_IDS:
            ADMIN_IDS.append(DEFAULT_ADMIN_ID)
    except ValueError:
        logger.error("Invalid DEFAULT_ADMIN_ID format. Use an integer.")

# Database file path
DATABASE_FILE = 'computer_repair_bot.db'
