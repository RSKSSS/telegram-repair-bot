import os
import time
import telepot
import logging
from telepot.loop import MessageLoop
from database import initialize_database
from bot import setup_handlers
from config import TELEGRAM_BOT_TOKEN

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No bot token provided. Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Initialize database
    initialize_database()
    
    logger.info("Starting Computer Repair Service Bot with telepot")
    
    # Create the bot
    bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
    
    # Delete any existing webhook first
    bot.deleteWebhook()
    
    # Setup handlers for messages and callbacks
    handlers = setup_handlers(bot)
    
    # Set up message handler
    MessageLoop(bot, handlers).run_as_thread()
    logger.info("Bot is listening...")
    
    # Keep the program running
    while True:
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Bot stopped")
            break

if __name__ == '__main__':
    main()
