"""
Основной модуль приложения для запуска веб-сервера Flask
и Telegram бота в среде Render или локально.
"""

import os
import logging
from app import app
from database import initialize_database as db_initialize
from bot_diagnostics import bot_polling, run_bot_diagnostics

# Настройка логирования
logger = logging.getLogger(__name__)

# Эта функция необходима для render_app.py
def initialize_database():
    """Функция-обертка для инициализации базы данных
    Вызывает соответствующую функцию из модуля database"""
    logger.info("Инициализация базы данных через main.py...")
    return db_initialize()

# Получаем токен бота либо из переменных окружения, либо используем фиксированный токен
def get_bot_token():
    """Получение токена бота из переменных окружения или использование фиксированного токена"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token and ':' in token:
        logger.info(f"Использую токен из переменных окружения (длина: {len(token)})")
        return token
    else:
        from shared_state import TOKEN
        logger.info(f"Использую фиксированный токен из shared_state (длина: {len(TOKEN)})")
        return TOKEN

# Эта функция запускает бота и нужна для render_app.py
def start_bot():
    """
    Запуск бота с использованием функции из bot_diagnostics.py
    """
    from start_bot import start_bot as starter
    return starter()

if __name__ == "__main__":
    # Запускаем только веб-сервер Flask на порту 5000
    app.run(host='0.0.0.0', port=5000)