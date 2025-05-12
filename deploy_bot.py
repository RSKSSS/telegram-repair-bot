#!/usr/bin/env python
"""
Безопасный запуск Telegram-бота с единственным экземпляром 
и системой оповещения администраторов об ошибках.

Этот файл используется для деплоя бота на Render.
"""
import os
import sys
import time
import signal
import socket
import tempfile
import logging
import traceback
from datetime import datetime

# Настраиваем основное логирование
try:
    # Пытаемся импортировать настроенные логгеры
    from setup_logging import main_logger as logger, error_logger
except ImportError:
    # Если не удалось, создаем базовый логгер
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('deploy_bot')
    error_logger = logger

def ensure_single_instance():
    """
    Проверяет, что запущен только один экземпляр бота.
    Если обнаружен другой экземпляр, завершает текущий процесс.
    
    Returns:
        bool: True, если это единственный экземпляр, иначе завершает процесс
    """
    # Создаем временный файл
    lock_file = os.path.join(tempfile.gettempdir(), "telegram_bot.lock")
    
    # Пытаемся создать сокет на определенном порту
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Порт для проверки единственного экземпляра (можно изменить)
        port = 51234
        sock.bind(('localhost', port))
        
        # Записываем PID в файл
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Регистрируем функцию очистки при завершении
        def cleanup():
            try:
                sock.close()
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except Exception as e:
                logger.error(f"Ошибка при очистке: {e}")
        
        # Регистрируем обработчики сигналов
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, lambda s, f: (cleanup(), sys.exit(0)))
        
        return True
    
    except socket.error:
        # Порт занят, значит, другой экземпляр уже запущен
        logger.warning("Обнаружен другой запущенный экземпляр бота!")
        
        # Проверяем, жив ли процесс
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Проверяем, существует ли процесс
                try:
                    os.kill(pid, 0)  # Не убивает процесс, только проверяет
                    logger.warning(f"Бот уже запущен (PID: {pid})")
                    print(f"⚠️ Бот уже запущен (PID: {pid})! Завершаем текущий процесс.")
                    sys.exit(1)
                except OSError:
                    # Процесс не существует, удаляем файл
                    logger.info(f"Процесс {pid} не существует, удаляем lock-файл")
                    os.remove(lock_file)
                    # Повторяем попытку
                    return ensure_single_instance()
            except Exception as e:
                logger.error(f"Ошибка при проверке PID: {e}")
        
        sock.close()
        print("⚠️ Бот уже запущен! Завершаем текущий процесс.")
        sys.exit(1)

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

def setup_error_handlers(bot):
    """
    Настраивает обработчики ошибок для бота
    
    Args:
        bot: Экземпляр Telegram-бота
    """
    from telebot.apihelper import ApiTelegramException
    from admin_notifications import notify_error
    
    @bot.middleware_handler(update_types=['message', 'callback_query'])
    def error_catching_middleware(bot_instance, update):
        """Промежуточный обработчик для перехвата ошибок"""
        try:
            # Просто пропускаем сообщение дальше
            return update
        except Exception as e:
            # Обрабатываем исключение
            error_traceback = traceback.format_exc()
            error_logger.error(f"Ошибка при обработке сообщения: {e}\n{error_traceback}")
            
            # Извлекаем ID пользователя из обновления
            user_id = None
            context = {}
            
            if hasattr(update, 'message') and update.message:
                user_id = update.message.from_user.id
                context['chat_id'] = update.message.chat.id
                if update.message.text:
                    context['message_text'] = update.message.text
            elif hasattr(update, 'callback_query') and update.callback_query:
                user_id = update.callback_query.from_user.id
                if update.callback_query.data:
                    context['callback_data'] = update.callback_query.data
            
            # Отправляем уведомление администратору
            notify_error(
                f"Ошибка при обработке сообщения: {e}", 
                exception=e,
                user_id=user_id,
                context=context
            )
            
            # Возвращаем обновление для продолжения обработки
            return update
    
    # Логирование всех исключений
    old_process_new_updates = bot.process_new_updates
    
    def process_new_updates_with_logging(updates):
        """Переопределенная функция обработки обновлений с логированием"""
        try:
            return old_process_new_updates(updates)
        except ApiTelegramException as e:
            error_logger.error(f"Ошибка API Telegram: {e}")
            notify_error(f"Ошибка API Telegram: {e}", exception=e)
            raise
        except Exception as e:
            error_logger.error(f"Необработанная ошибка: {e}")
            error_traceback = traceback.format_exc()
            error_logger.error(error_traceback)
            notify_error(f"Необработанная ошибка: {e}", exception=e)
            raise
    
    # Заменяем метод обработки обновлений
    bot.process_new_updates = process_new_updates_with_logging

def wait_for_internet():
    """
    Ожидает подключения к интернету перед запуском бота
    """
    logger.info("Проверка подключения к интернету...")
    max_attempts = 10
    attempt = 0
    delay = 5  # начальная задержка в секундах
    
    while attempt < max_attempts:
        try:
            # Проверяем доступность Telegram API
            socket.create_connection(("api.telegram.org", 443), timeout=10)
            logger.info("Подключение к интернету установлено")
            return True
        except OSError:
            attempt += 1
            logger.warning(f"Попытка {attempt}/{max_attempts}: Нет подключения к интернету. Повторная попытка через {delay} сек.")
            time.sleep(delay)
            # Увеличиваем задержку с каждой попыткой, но не более 30 секунд
            delay = min(delay * 1.5, 30)
    
    logger.error("Не удалось подключиться к интернету после нескольких попыток")
    return False

def run_with_error_handling():
    """
    Запускает бота с обработкой ошибок
    """
    # Проверяем подключение к интернету
    if not wait_for_internet():
        logger.critical("Запуск бота отменен из-за отсутствия подключения к интернету")
        sys.exit(1)

    # Проверяем, что это единственный запущенный экземпляр
    if not ensure_single_instance():
        return
    
    logger.info("Запуск бота с обработкой ошибок и проверкой единственного экземпляра")
    
    try:
        # Инициализируем модуль логирования
        import setup_logging
        logger.info("Система логирования инициализирована")
        
        # Импортируем необходимые модули
        from working_bot import bot
        
        # Настраиваем обработчики ошибок
        setup_error_handlers(bot)
        logger.info("Обработчики ошибок установлены")
        
        # Отправляем уведомление о запуске
        send_startup_notification()
        
        # Запускаем бота в бесконечном цикле с обработкой ошибок
        logger.info("Запуск бота в режиме polling...")
        
        while True:
            try:
                bot.polling(none_stop=True, interval=1, timeout=60)
            except Exception as e:
                error_logger.error(f"Ошибка при выполнении polling: {e}")
                from admin_notifications import notify_error
                notify_error(f"Бот перезапущен из-за ошибки: {e}", exception=e)
                
                # Пауза перед повторной попыткой
                time.sleep(10)
                
                # Повторный запуск только если это не ошибка конфликта экземпляров
                if "terminated by other getUpdates request" in str(e):
                    error_logger.critical("Обнаружен конфликт экземпляров, останавливаем бота")
                    sys.exit(1)
    
    except ImportError as e:
        logger.critical(f"Ошибка импорта модулей: {e}")
        sys.exit(1)
    except Exception as e:
        error_logger.critical(f"Критическая ошибка при запуске бота: {e}")
        error_traceback = traceback.format_exc()
        error_logger.critical(error_traceback)
        sys.exit(1)

if __name__ == '__main__':
    # Запускаем бота с обработкой ошибок
    run_with_error_handling()