#!/usr/bin/env python3
"""
Файл для запуска приложения на Render

Этот скрипт запускает и веб-сервер Flask, и Telegram бота в отдельных потоках,
используя правильную настройку и инициализацию всех компонентов.
"""

import os
import logging
import threading
import traceback
from main import app, initialize_database
from bot_diagnostics import bot_polling, run_bot_diagnostics

# Настройка логирования
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Получаем порт из переменных окружения Render
port = int(os.environ.get("PORT", 10000))

def run_bot_in_thread():
    """
    Запускает бота в отдельном потоке с обработкой ошибок
    """
    try:
        logger.info("Запуск диагностики бота перед запуском...")
        diagnostics = run_bot_diagnostics()
        
        if not diagnostics["database_connection"]:
            logger.error("❌ ОШИБКА: Не удалось подключиться к базе данных! Бот не будет запущен.")
            return
            
        if not diagnostics["bot_token_valid"]:
            logger.error("❌ ОШИБКА: Невалидный токен бота! Бот не будет запущен.")
            return
            
        logger.info("✅ Диагностика успешна! Запуск бота...")
        bot_polling()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        initialize_database()
        logger.info("База данных инициализирована")
        
        # Проверяем наличие и валидность токена
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("ОШИБКА: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        elif ':' not in token:
            logger.error(f"ОШИБКА: Невалидный формат токена. Токен должен содержать двоеточие (:). Текущая длина: {len(token)}")
        else:
            logger.info(f"Токен Telegram бота найден, длина: {len(token)} символов, формат корректный")
        
        # Запускаем бота в отдельном потоке
        logger.info("Запуск бота в отдельном потоке...")
        bot_thread = threading.Thread(target=run_bot_in_thread)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Поток бота запущен")
        
        # Запускаем Flask-приложение на указанном порту
        logger.info(f"Запуск веб-сервера на порту {port}...")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Критическая ошибка в основном потоке: {e}")
        logger.error(traceback.format_exc())