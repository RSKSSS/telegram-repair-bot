#!/usr/bin/env python
"""
Главный файл запуска бота и Flask приложения на разных портах.
"""

import os
import sys
import logging
import threading
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_flask_app():
    """Запускает Flask приложение на порту 5001"""
    try:
        logger.info("Запуск Flask на порту 5001...")
        os.environ['FLASK_PORT'] = '5001'
        import flask_app
        flask_app.app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Ошибка запуска Flask: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run_telegram_bot():
    """Запускает Telegram бота"""
    try:
        logger.info("Запуск Telegram бота...")
        # Импортируем исправленную версию файла запуска бота
        if os.path.exists('main_telegram_bot_fixed.py'):
            # Используем исправленную версию, если она существует
            sys.path.insert(0, os.getcwd())
            from main_telegram_bot_fixed import main
            main()
        else:
            # Используем оригинальную версию, если исправленной нет
            from main_telegram_bot import main
            main()
    except Exception as e:
        logger.error(f"Ошибка запуска Telegram бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """
    Основная функция запуска, которая запускает Flask и бота в разных потоках.
    """
    logger.info("===== Запуск приложения =====")
    
    # Ждем ввод пользователя перед запуском
    time.sleep(1)
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Даем Flask время на запуск
    time.sleep(2)
    
    # Запускаем Telegram бота в основном потоке
    run_telegram_bot()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Программа не запущена из-за ошибок!")
        sys.exit(1)
    else:
        logger.info("Программа успешно запущена!")