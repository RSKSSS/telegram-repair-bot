#!/usr/bin/env python
"""
Простой скрипт для запуска только Telegram бота без веб-сервера
"""

import os
import logging
import telebot
from shared_state import TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Создаем экземпляр бота
        bot = telebot.TeleBot(TOKEN)
        logger.info(f"Создан экземпляр бота с токеном длиной {len(TOKEN)}")
        
        # Регистрируем обработчики
        @bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            bot.reply_to(message, "Бот для сервиса ремонта компьютеров запущен и работает!")
            
        @bot.message_handler(commands=['test'])
        def handle_test(message):
            bot.reply_to(message, "Тестовый режим: бот отвечает на сообщения!")
            
        @bot.message_handler(commands=['ping'])
        def handle_ping(message):
            bot.reply_to(message, "Pong! Бот активен.")
            
        @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            bot.reply_to(message, f"Бот получил сообщение: {message.text}")
        
        # Запускаем бота
        logger.info("Запуск бота в режиме polling...")
        bot.infinity_polling()
        logger.info("Бот остановлен")
        
        return True
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("ЗАПУСК ТОЛЬКО TELEGRAM БОТА (БЕЗ ВЕБ-СЕРВЕРА)...")
    success = main()
    
    if not success:
        print("Ошибка при запуске бота!")
        import sys
        sys.exit(1)