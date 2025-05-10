#!/usr/bin/env python3
"""
Исправленный файл запуска telegram-бота без веб-сервера Flask
"""

import os
import sys
import logging
import traceback
from start_bot import start_bot

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Запуск только Telegram бота без веб-сервера...")
        # Запускаем бота
        success = start_bot()
        
        if success:
            logger.info("Telegram бот успешно запущен!")
        else:
            logger.error("Ошибка при запуске бота!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()