#!/usr/bin/env python
"""
Минимальный скрипт для запуска только Telegram бота
"""

import os
import sys
import logging
import telebot

# Принудительно отключаем попытки запуска Flask
os.environ["NO_FLASK"] = "true"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем токен напрямую из переменной окружения или используем захардкоженный токен
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") 
if not TOKEN or len(TOKEN) < 5:
    TOKEN = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ12345678"  # Фиктивный токен

def main():
    try:
        logger.info(f"Запуск бота с токеном длиной {len(TOKEN)}")
        
        # Создаем экземпляр бота
        bot = telebot.TeleBot(TOKEN)
        
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
        
        return True
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("ЗАПУСК МИНИМАЛЬНОГО TELEGRAM БОТА...")
    success = main()
    
    if not success:
        print("Ошибка при запуске бота!")
        sys.exit(1)