"""
Универсальный скрипт для запуска бота на любом хостинге
"""
import os
import sys
import time
import logging
import traceback
import signal
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('deploy')

# Проверка наличия токена бота
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    logger.info("Будет использован резервный токен из shared_state.py")

def setup_signal_handlers():
    """Настраивает обработчики сигналов для корректного завершения"""
    def signal_handler(sig, frame):
        logger.info(f"Получен сигнал {sig}, завершаем работу...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def check_environment():
    """Проверяет и выводит информацию об окружении"""
    logger.info("=== Информация об окружении ===")
    
    # Проверка переменных окружения
    if TOKEN:
        logger.info(f"✅ TELEGRAM_BOT_TOKEN найден (длина: {len(TOKEN)})")
    else:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    
    # Информация о платформе
    import platform
    logger.info(f"Система: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    
    # Определение хостинга
    if os.environ.get('RENDER'):
        logger.info("Хостинг: Render")
    elif os.environ.get('PYTHONANYWHERE_SITE'):
        logger.info("Хостинг: PythonAnywhere")
    elif os.environ.get('RAILWAY_STATIC_URL'):
        logger.info("Хостинг: Railway")
    else:
        logger.info("Хостинг: Локальный запуск или неизвестный хостинг")

def start_bot():
    """Запускает Telegram бота"""
    try:
        # Импортируем модуль запуска бота
        from working_bot import start_bot_polling
        
        # Запускаем бота
        logger.info("Запуск бота...")
        start_bot_polling()
        
    except ImportError:
        logger.error("Не удалось импортировать working_bot.py!")
        logger.info("Пробуем запустить бота напрямую...")
        
        try:
            # Импортируем бота напрямую
            from shared_state import bot
            
            # Запускаем бота
            logger.info("Запуск бота напрямую...")
            bot.polling(none_stop=True, interval=1, timeout=60)
            
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            logger.error(traceback.format_exc())
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        return False
    
    return True

def main():
    """Основная функция запуска"""
    try:
        # Выводим информацию о запуске
        logger.info("=== Запуск Telegram бота ===")
        logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Настраиваем обработчики сигналов
        setup_signal_handlers()
        
        # Проверяем окружение
        check_environment()
        
        # Проверяем запуск на Replit и активируем keep_alive
        if 'REPLIT_DB_URL' in os.environ:
            logger.info("Обнаружен запуск на Replit, активируем keep_alive...")
            try:
                from keep_alive import keep_alive
                keep_alive()
                logger.info("Веб-сервер keep_alive успешно запущен")
            except Exception as e:
                logger.warning(f"Не удалось запустить keep_alive: {e}")
        
        # Запускаем бота
        if not start_bot():
            logger.error("Не удалось запустить бота!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Добавляем небольшую задержку перед запуском
    # Это может помочь на некоторых хостингах
    time.sleep(2)
    main()