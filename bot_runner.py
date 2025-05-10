#!/usr/bin/env python
"""
Скрипт для прямого запуска только Telegram бота
Этот скрипт не пытается запустить Flask-сервер
"""

import os
import sys
import logging
import signal
import traceback
from shared_state import TOKEN

def run_bot():
    try:
        import telebot
        from telebot.types import Message
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger("bot_runner")
        
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
        
        # Обработчик сигналов для корректного завершения
        def signal_handler(sig, frame):
            logger.info("Получен сигнал завершения, останавливаем бота...")
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем бота
        logger.info("Запуск бота в режиме polling...")
        bot.infinity_polling()
        logger.info("Бот остановлен")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    print("ЗАПУСК TELEGRAM БОТА (БЕЗ ВЕБ-СЕРВЕРА)...")
    success = run_bot()
    
    if not success:
        print("Ошибка при запуске бота!")
        sys.exit(1)