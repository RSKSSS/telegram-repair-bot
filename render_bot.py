"""
Запуск Telegram бота на Render с обработкой ошибок и защитой от дублей
"""
import os
import sys
import time
import logging
import traceback
import fcntl
import signal
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('render_bot')

# Путь к lock-файлу
LOCK_FILE = "/tmp/render_telegram_bot.lock"

def obtain_lock():
    """
    Пытается получить блокировку, чтобы убедиться, что запущен только один экземпляр бота
    
    Returns:
        bool: True если блокировка получена, False если уже запущен другой экземпляр
    """
    try:
        # Открываем файл блокировки
        lock_file_descriptor = open(LOCK_FILE, 'w')
        
        # Пытаемся получить эксклюзивную блокировку без ожидания
        fcntl.lockf(lock_file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # Записываем PID процесса в файл
        lock_file_descriptor.write(str(os.getpid()))
        lock_file_descriptor.flush()
        
        # Сохраняем дескриптор файла открытым, пока программа работает
        # Это важно, иначе блокировка будет освобождена
        return lock_file_descriptor
    
    except IOError:
        # Не удалось получить блокировку - уже запущен другой экземпляр
        logger.warning("Не удалось получить блокировку - уже запущен другой экземпляр бота")
        return False
    
    except Exception as e:
        logger.error(f"Ошибка при получении блокировки: {e}")
        return False

def main():
    """
    Основная функция запуска бота на Render
    """
    try:
        # Проверяем, запущен ли уже бот
        lock_fd = obtain_lock()
        if not lock_fd:
            logger.error("Уже запущен другой экземпляр бота. Завершаем текущий процесс.")
            print("⚠️ Уже запущен другой экземпляр бота. Завершаем текущий процесс.")
            # Небольшая задержка перед выходом
            time.sleep(3)
            sys.exit(1)
        
        # Регистрируем функцию очистки при завершении
        def cleanup(sig, frame):
            logger.info(f"Получен сигнал {sig}, завершаем работу...")
            try:
                # Закрываем файл блокировки
                if lock_fd:
                    lock_fd.close()
                # Удаляем файл блокировки
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
            except Exception as e:
                logger.error(f"Ошибка при очистке: {e}")
            sys.exit(0)
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)
        
        # Импортируем и запускаем бота
        try:
            from bot_starter import main as start_bot
            start_bot()
        except ImportError:
            # Если bot_starter не найден, пытаемся запустить напрямую из working_bot
            try:
                from working_bot import start_bot_polling
                logger.info("Запуск бота через working_bot.start_bot_polling...")
                start_bot_polling()
            except Exception as e:
                logger.error(f"Ошибка при запуске бота: {e}")
                error_traceback = traceback.format_exc()
                logger.error(error_traceback)
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        sys.exit(1)

if __name__ == "__main__":
    main()