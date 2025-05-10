#!/usr/bin/env python
"""
Специальная версия запуска Telegram бота для Render без конфликта с Flask-сервером.
Эта версия предназначена для работы в среде Render, где могут быть проблемы с портами.
"""

import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler

# Настройка логирования
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Добавляем вывод в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# Добавляем вывод в файл logs/render_bot.log с ротацией
os.makedirs('logs', exist_ok=True)
file_handler = RotatingFileHandler('logs/render_bot.log', maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

def main():
    """
    Основная функция запуска бота для Render
    """
    try:
        logger.info("===== Запуск Telegram бота в режиме Render =====")
        
        # Импортируем необходимые зависимости
        from database import initialize_database
        from shared_state import TOKEN, bot
        
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        initialize_database()
        logger.info("База данных инициализирована")
        
        # Проверяем токен
        if not TOKEN or ':' not in TOKEN:
            logger.error(f"Невалидный токен бота: {TOKEN if TOKEN else 'токен отсутствует'}")
            return 1
            
        logger.info(f"Токен бота корректный, длина: {len(TOKEN)} символов")
        
        # Запускаем бота через start_bot.py
        logger.info("Запуск бота через модуль start_bot...")
        from start_bot import start_bot
        success = start_bot()
        
        if success:
            logger.info("Бот успешно запущен!")
            return 0
        else:
            logger.error("Ошибка при запуске бота!")
            return 1
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    """
    Точка входа для запуска бота в режиме Render
    """
    exitcode = main()
    sys.exit(exitcode)