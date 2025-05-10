#!/usr/bin/env python3
"""
Запуск только бота без веб-сервера и без каких-либо импортов Flask
"""

import os
import sys
import logging
import traceback
import subprocess

# Настройка логирования
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_bot():
    """
    Запускает минимальную версию бота в изолированном процессе
    """
    try:
        logger.info("Запуск минимальной версии бота...")
        
        # Запускаем процесс с минимальным ботом
        bot_process = subprocess.Popen([sys.executable, "minimal_bot.py"])
        
        # Ждем завершения процесса
        exit_code = bot_process.wait()
        
        if exit_code == 0:
            logger.info("Бот успешно завершил работу")
            return True
        else:
            logger.error(f"Бот завершил работу с кодом ошибки: {exit_code}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_bot()
    if not success:
        sys.exit(1)