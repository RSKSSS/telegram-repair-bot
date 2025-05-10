#!/usr/bin/env python
"""
Скрипт для запуска только Telegram бота без веб-сервера

При запуске этого файла запускается только бот без веб-сервера,
что позволяет избежать конфликта портов.
"""

import os
import sys
import logging
from database import initialize_database
from bot_diagnostics import bot_polling, run_bot_diagnostics
from logger import get_component_logger

# Настройка логирования
logger = get_component_logger("telegram_bot_runner")
logger.setLevel(logging.INFO)

print("Запуск скрипта run_telegram_bot.py...")

if __name__ == "__main__":
    print("Запуск Telegram бота без веб-сервера...")
    
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    initialize_database()
    logger.info("База данных инициализирована")
    
    # Запускаем диагностику
    logger.info("Запуск диагностики бота...")
    diagnostics = run_bot_diagnostics()
    
    if diagnostics["errors"]:
        logger.error(f"Обнаружены ошибки при диагностике: {len(diagnostics['errors'])}")
        for i, error in enumerate(diagnostics["errors"], 1):
            logger.error(f"  Ошибка {i}: {error}")
        sys.exit(1)
    
    # Запуск бота
    logger.info("Запуск Telegram бота...")
    bot_polling()