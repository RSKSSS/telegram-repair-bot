#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота с Flask на порту 5001
"""

import os
import sys
import logging
import threading
import telebot
from telebot.types import Message

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

def run_bot():
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
        
        return True
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Запускаем бота в отдельном потоке
def run_bot_thread():
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    logger.info("Поток бота запущен")
    return bot_thread

# Создаем минимальное Flask-приложение на другом порту
from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот запущен и работает!"

if __name__ == "__main__":
    print("ЗАПУСК TELEGRAM БОТА С FLASK НА ПОРТУ 5001...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = run_bot_thread()
    
    # Запускаем Flask на порту 5001
    app.run(host='0.0.0.0', port=5001)