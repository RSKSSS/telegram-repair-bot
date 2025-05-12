"""
Улучшенный Telegram бот с проверкой запущенных экземпляров
и системой логирования ошибок с оповещениями администраторов
"""
import os
import sys
import time
import logging
import traceback
import tempfile
import socket
import signal
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

# Настройка логирования
LOG_FOLDER = 'logs'
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Создаем основной логгер
logger = logging.getLogger('telegram_bot')
logger.setLevel(logging.DEBUG)

# Создаем файловый обработчик с ротацией (макс. 5 МБ, 5 файлов)
file_handler = RotatingFileHandler(
    os.path.join(LOG_FOLDER, 'bot.log'),
    maxBytes=5*1024*1024,  # 5 МБ
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Создаем консольный обработчик
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Создаем специальный обработчик для критических ошибок
error_file_handler = RotatingFileHandler(
    os.path.join(LOG_FOLDER, 'errors.log'),
    maxBytes=2*1024*1024,  # 2 МБ
    backupCount=3
)
error_file_handler.setLevel(logging.ERROR)

# Форматирование логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
error_file_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(error_file_handler)

# Глобальный обработчик необработанных исключений
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Стандартное поведение для KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Формируем информацию об ошибке
    error_msg = f"Необработанное исключение: {exc_type.__name__}: {exc_value}"
    error_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Логируем ошибку
    logger.critical(f"{error_msg}\n{error_traceback}")
    
    # Отправляем уведомление администратору (будет реализовано позже)
    send_error_notification_to_admin(error_msg, error_traceback)

# Устанавливаем глобальный обработчик исключений
sys.excepthook = handle_uncaught_exception

# Функция для отправки уведомлений админам об ошибках
def send_error_notification_to_admin(error_msg, error_traceback=None):
    """
    Отправляет уведомление администраторам о критической ошибке
    
    Args:
        error_msg: Краткое описание ошибки
        error_traceback: Полный стек вызовов (опционально)
    """
    # Импортируем функции из основного бота
    try:
        from working_bot import get_user_role
        from config import ROLES
        from database import get_all_users
    except ImportError:
        logger.error("Не удалось импортировать функции для отправки уведомлений")
        return
    
    # Получаем всех администраторов
    try:
        users = get_all_users()
        admin_ids = []
        
        # Проверяем каждого пользователя на роль администратора
        for user in users:
            try:
                user_id = user.get('user_id') or user.get('id')
                if user_id and get_user_role(user_id) == ROLES['ADMIN']:
                    admin_ids.append(user_id)
            except Exception as e:
                logger.error(f"Ошибка при проверке администратора: {e}")
        
        # Если администраторы не найдены, логируем это
        if not admin_ids:
            logger.warning("Администраторы не найдены для отправки уведомления об ошибке")
            return
        
        # Формируем сообщение
        error_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        message = f"🚨 *КРИТИЧЕСКАЯ ОШИБКА!* 🚨\n\n"
        message += f"⏰ *Время*: {error_time}\n"
        message += f"❌ *Описание*: {error_msg}\n\n"
        
        # Добавляем стек вызовов, если он есть (короткая версия)
        if error_traceback:
            # Ограничиваем длину, чтобы сообщение не было слишком большим
            max_length = 500
            if len(error_traceback) > max_length:
                error_traceback = error_traceback[:max_length] + "...\n[Сообщение обрезано]"
            message += f"📋 *Детали*:\n`{error_traceback}`"
        
        # Отправляем уведомление каждому администратору
        from shared_state import bot
        if bot:
            for admin_id in admin_ids:
                try:
                    bot.send_message(admin_id, message, parse_mode="Markdown")
                    logger.info(f"Уведомление об ошибке отправлено администратору {admin_id}")
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об ошибке: {e}")

# Проверка единственного экземпляра бота
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

def run_bot_with_error_handling():
    """
    Запускает бота с обработкой ошибок и уведомлениями
    """
    # Проверяем, что это единственный запущенный экземпляр
    if not ensure_single_instance():
        return
    
    logger.info("Запуск бота с обработкой ошибок и проверкой единственного экземпляра")
    
    # Пытаемся импортировать и запустить основной бот
    try:
        from working_bot import start_bot_polling, bot
        
        # Оборачиваем запуск бота в обработчик ошибок
        try:
            # Дополнительный обработчик сообщений для отлова ошибок
            @bot.middleware_handler(update_types=['message', 'callback_query'])
            def error_catching_middleware(bot_instance, update):
                try:
                    # Просто пропускаем сообщение дальше
                    return update
                except Exception as e:
                    # Обрабатываем исключение
                    logger.error(f"Ошибка при обработке сообщения: {e}")
                    error_traceback = traceback.format_exc()
                    logger.error(error_traceback)
                    
                    # Отправляем уведомление администратору
                    send_error_notification_to_admin(f"Ошибка при обработке сообщения: {e}", error_traceback)
                    
                    # Возвращаем обновление для продолжения обработки
                    return update
            
            # Запускаем бот
            start_bot_polling()
            
        except ApiTelegramException as e:
            if "terminated by other getUpdates request" in str(e):
                logger.error("Уже запущен другой экземпляр бота с тем же токеном!")
                print("⚠️ Уже запущен другой экземпляр бота с тем же токеном! Завершаем процесс.")
                sys.exit(1)
            else:
                logger.error(f"Ошибка API Telegram: {e}")
                send_error_notification_to_admin(f"Ошибка API Telegram: {e}")
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            error_traceback = traceback.format_exc()
            logger.error(error_traceback)
            send_error_notification_to_admin(f"Ошибка при запуске бота: {e}", error_traceback)
    
    except ImportError as e:
        logger.error(f"Ошибка импорта модулей: {e}")
        print(f"⚠️ Ошибка импорта модулей: {e}")
        send_error_notification_to_admin(f"Ошибка импорта модулей: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Запускаем бота с обработкой ошибок
    run_bot_with_error_handling()