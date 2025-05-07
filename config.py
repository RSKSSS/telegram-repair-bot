import os

# Database configuration
DATABASE_FILE = 'service_bot.db'

# Telegram bot token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Status options for orders
ORDER_STATUSES = ['new', 'processing', 'completed', 'cancelled']

# User roles
USER_ROLES = ['client', 'admin']