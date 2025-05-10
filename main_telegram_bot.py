#!/usr/bin/env python
"""
Главный файл запуска Telegram бота для Replit.
Этот файл объединяет минимальный бот и проверки для Render.
"""

import os
import sys
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Основная функция запуска, которая выбирает подходящий режим работы.
    В Render запускает версию для Render, в остальных случаях - минимальную.
    """
    logger.info("===== Запуск Telegram бота =====")
    
    # Проверяем переменную окружения RENDER для определения среды
    if os.environ.get('RENDER') == 'true':
        logger.info("Обнаружена среда Render, запускаем специальную версию...")
        try:
            import main_render
            return main_render.main()
        except ImportError:
            logger.error("Не удалось импортировать main_render.py, пробуем минимальную версию...")
            time.sleep(2)  # Задержка для стабилизации логов
    
    # Если не Render или произошла ошибка с main_render.py, 
    # запускаем минимальную версию
    logger.info("Запускаем минимальную версию бота...")
    try:
        import minimal_bot
        return minimal_bot.main()
    except ImportError:
        logger.error("Не удалось импортировать minimal_bot.py!")
        # Пробуем запустить оригинальный скрипт
        try:
            logger.info("Пробуем запустить через стандартный main.py...")
            from start_bot import start_bot
            return start_bot()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            return False

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Бот не запущен из-за ошибок!")
        sys.exit(1)
    else:
        logger.info("Бот успешно запущен!")