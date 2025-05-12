"""
Модуль для безопасного запуска бота с проверкой дублирующихся экземпляров
"""
import os
import sys
import time
import logging
import traceback
import socket
import signal
from datetime import datetime
from telebot.apihelper import ApiTelegramException

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot_starter')

# Импортируем необходимые модули
try:
    from shared_state import bot
    logger.info("Бот успешно импортирован из shared_state")
except ImportError as e:
    logger.error(f"Ошибка при импорте бота: {e}")
    sys.exit(1)

def start_bot_polling():
    """
    Безопасно запускает бота в режиме polling с обработкой ошибок
    
    Returns:
        bool: True если запуск успешен, False если произошла ошибка
    """
    try:
        logger.info("Запуск бота в режиме polling...")
        # Используем настройки для более надежного соединения
        bot.polling(none_stop=True, interval=1, timeout=60)
        return True
    except ApiTelegramException as e:
        if "terminated by other getUpdates request" in str(e):
            logger.error("Уже запущен другой экземпляр бота с тем же токеном!")
            print("⚠️ Уже запущен другой экземпляр бота с тем же токеном! Завершаем процесс.")
            # Добавляем задержку перед завершением, чтобы не создавать циклы перезапуска
            time.sleep(5)
            sys.exit(1)
        else:
            logger.error(f"Ошибка API Telegram: {e}")
            return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при запуске бота: {e}")
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        return False

def send_startup_notification():
    """Отправляет уведомление о запуске бота администраторам"""
    try:
        from admin_notifications import notify_info
        
        # Получаем информацию о системе
        hostname = socket.gethostname()
        environment = os.environ.get('RENDER', 'development')
        python_version = sys.version.split()[0]
        
        # Формируем сообщение
        message = f"🚀 Бот успешно запущен!\n\n"
        message += f"⏰ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        message += f"🌐 Среда: {environment}\n"
        message += f"💻 Сервер: {hostname}\n"
        message += f"🐍 Python: {python_version}\n"
        
        # Отправляем уведомление
        notify_info(message, force=True)
        
        logger.info("Отправлено уведомление о запуске бота")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о запуске: {e}")

def main():
    """Основная функция запуска бота"""
    try:
        # Регистрируем обработчики сигналов для корректного завершения
        def signal_handler(sig, frame):
            logger.info(f"Получен сигнал {sig}, завершаем работу...")
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем бота
        logger.info("Запуск бота...")
        
        # Импортируем все обработчики, если нужно
        # Важно импортировать их здесь, чтобы все обработчики были зарегистрированы
        try:
            import working_bot
            from ai_commands import register_ai_commands
            
            # Регистрируем ИИ команды
            register_ai_commands(bot)
            
            # Отправляем уведомление о запуске (если нужно)
            send_startup_notification()
            
            # Запускаем бота
            success = start_bot_polling()
            
            if not success:
                logger.error("Не удалось запустить бота, завершаем работу...")
                sys.exit(1)
                
        except ImportError as e:
            logger.error(f"Ошибка при импорте модулей: {e}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        sys.exit(1)

if __name__ == "__main__":
    main()