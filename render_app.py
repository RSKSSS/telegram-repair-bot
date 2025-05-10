#!/usr/bin/env python3
"""
Файл для запуска приложения на Render
"""

import os
import logging
import threading
from main import app, initialize_database, bot_polling

# Настройка логирования
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Получаем порт из переменных окружения Render
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    # Инициализируем базу данных
    logger.info("Инициализация базы данных...")
    initialize_database()
    logger.info("База данных инициализирована")
    
    # Проверяем наличие токена
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        logger.error("ОШИБКА: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
    else:
        logger.info(f"Токен Telegram бота найден, длина: {len(os.environ.get('TELEGRAM_BOT_TOKEN'))} символов")
    
    # Запускаем бота в отдельном потоке
    logger.info("Запуск бота в отдельном потоке...")
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    logger.info("Бот запущен")
    
    # Запускаем Flask-приложение на указанном порту
    logger.info(f"Запуск веб-сервера на порту {port}...")
    app.run(host="0.0.0.0", port=port)