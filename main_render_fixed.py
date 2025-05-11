#!/usr/bin/env python
"""
Специальный файл для запуска на платформе Render.
Исправленная версия с учетом синтаксических ошибок и конфликта портов.
"""

import os
import sys
import logging
import traceback
from threading import Thread
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_flask_app():
    """Запуск Flask приложения на порту 5001"""
    try:
        # Устанавливаем порт для Flask
        os.environ['FLASK_PORT'] = '5001'
        logger.info("Запуск Flask на порту 5001...")
        import flask_app
        flask_app.app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Ошибка при запуске Flask: {e}")
        logger.error(traceback.format_exc())

def start_bot():
    """Запуск телеграм-бота"""
    try:
        # Используем исправленную версию start_bot.py
        logger.info("Запуск телеграм-бота...")
        # Импортируем исправленную версию start_bot.py
        if os.path.exists('start_bot_fixed.py'):
            sys.path.insert(0, os.getcwd())
            from start_bot_fixed import start_bot
            start_bot()
        else:
            # Если исправленной версии нет, используем оригинальную
            from start_bot import start_bot
            start_bot()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())

def main():
    """Запуск приложения на Render"""
    logger.info("===== Запуск приложения на Render (исправленная версия) =====")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Даем время Flask запуститься
    time.sleep(2)
    
    # Запускаем телеграм-бота в основном потоке
    start_bot()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Ошибка запуска приложения на Render!")
        sys.exit(1)