import os
import time
import telepot
import logging
from telepot.loop import MessageLoop

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def handle_message(msg):
    """Handle incoming messages"""
    content_type, chat_type, chat_id = telepot.glance(msg)
    logger.info(f"Message from {chat_id}: {content_type}")
    
    if content_type == 'text':
        text = msg['text']
        
        if text.startswith('/start'):
            # Handle start command
            first_name = msg.get('from', {}).get('first_name', 'User')
            bot.sendMessage(chat_id, f'Здравствуйте, {first_name}! Добро пожаловать в сервис управления ремонтом компьютеров.')
        elif text.startswith('/help'):
            # Handle help command
            bot.sendMessage(chat_id, 'Используйте /start для начала работы.')
        else:
            # Echo all other messages
            bot.sendMessage(chat_id, f"Вы сказали: {text}")

def main():
    """Start the bot."""
    global bot
    
    if not TOKEN:
        logger.error("No bot token provided. Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    logger.info("Starting Computer Repair Service Bot with telepot")
    
    # Create the bot
    bot = telepot.Bot(TOKEN)
    
    # Delete any existing webhook first
    bot.deleteWebhook()
    
    # Set up message handler
    MessageLoop(bot, handle_message).run_as_thread()
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
