#!/usr/bin/env python
"""
Главный файл запуска Telegram бота для Replit.
Исправленная версия, которая использует исправленные файлы.
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
    В Render запускает исправленную версию для Render, в остальных случаях - минимальную.
    """
    logger.info("===== Запуск Telegram бота (ИСПРАВЛЕННАЯ ВЕРСИЯ) =====")
    
    # Проверяем переменную окружения RENDER для определения среды
    if os.environ.get('RENDER') == 'true':
        logger.info("Обнаружена среда Render, запускаем исправленную специальную версию...")
        try:
            # Используем исправленную версию для Render
            if os.path.exists('main_render_fixed.py'):
                import main_render_fixed
                return main_render_fixed.main()
            else:
                import main_render
                return main_render.main()
        except ImportError as e:
            logger.error(f"Не удалось импортировать модуль для Render: {e}")
            time.sleep(2)  # Задержка для стабилизации логов
    
    # В локальной среде запускаем полную версию бота
    logger.info("Запускаем полную версию бота...")
    try:
        # Используем исправленную версию start_bot.py
        if os.path.exists('start_bot_fixed.py'):
            # Используем исправленную версию, если она существует
            sys.path.insert(0, os.getcwd())
            from start_bot_fixed import start_bot
            logger.info("Используется исправленная версия start_bot_fixed.py")
            return start_bot()
        else:
            # Используем оригинальную версию, если исправленной нет
            from start_bot import start_bot
            logger.info("Используется оригинальная версия start_bot.py")
            return start_bot()
    except Exception as e:
        logger.error(f"Ошибка при запуске полной версии бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Если не удалось запустить полную версию, пробуем минимальную
        logger.info("Пробуем запустить минимальную версию бота...")
        try:
            import minimal_bot
            return minimal_bot.main()
        except Exception as e2:
            logger.error(f"Ошибка при запуске минимальной версии бота: {e2}")
            logger.error(traceback.format_exc())
            return False

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Бот не запущен из-за ошибок!")
        sys.exit(1)
    else:
        logger.info("Бот успешно запущен!")