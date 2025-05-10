"""
Запуск Telegram бота
"""

import os
import logging
from telebot import TeleBot
from config import TOKEN
from bot_fixed import handle_start_command, handle_help_command, handle_message, handle_callback_query
from logger import get_component_logger
from database import initialize_database

# Инициализация логирования
logger = get_component_logger("bot")
logger.setLevel(logging.INFO)

# Инициализация бота
if __name__ == "__main__":
    # Инициализация базы данных
    initialize_database()
    
    # Создаем экземпляр бота
    bot = TeleBot(TOKEN)
    
    # Регистрируем обработчики
    bot.register_message_handler(handle_start_command, commands=['start'])
    bot.register_message_handler(handle_help_command, commands=['help'])
    bot.register_message_handler(handle_message, func=lambda message: True, content_types=['text'])
    bot.register_callback_query_handler(handle_callback_query, func=lambda call: True)
    
    # Запускаем бота
    logger.info("Бот запущен и ожидает сообщений...")
    bot.infinity_polling()