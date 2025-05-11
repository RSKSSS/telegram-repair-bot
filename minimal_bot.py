#!/usr/bin/env python
"""
Минимальная версия Telegram бота для тестирования работоспособности в среде Render.
Этот файл содержит только базовую функциональность, необходимую для проверки 
возможности подключения к Telegram API и базе данных.
"""

import os
import sys
import logging
import telebot
import psycopg2
import sqlite3
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение токена бота
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN or ':' not in TOKEN:
    # Фиксированный токен для отладки (тот же, что в shared_state.py)
    TOKEN = "8158789441:AAGlPsdPmgTKXtugoa3qlVwb4ee2vW3mL9g"
    logger.info(f"Используется фиксированный токен (длина: {len(TOKEN)})")
else:
    logger.info(f"Используется токен из переменных окружения (длина: {len(TOKEN)})")

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Функция для определения типа базы данных
def is_postgres():
    """Проверяет, используется ли PostgreSQL"""
    # Проверяем специальную переменную окружения RENDER
    if os.environ.get('RENDER') == 'true':
        return True
    # Также проверяем наличие DATABASE_URL
    if os.environ.get('DATABASE_URL') and 'postgres' in os.environ.get('DATABASE_URL', ''):
        return True
    return False  # В локальной среде используем SQLite

# Функция для подключения к базе данных
def get_connection():
    """Получение соединения с базой данных (PostgreSQL или SQLite)"""
    try:
        # Проверяем, нужно ли использовать PostgreSQL
        if is_postgres():
            # В Render используем PostgreSQL
            logger.info("Подключение к PostgreSQL в среде Render...")
            database_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(database_url)
            return conn
        else:
            # В локальной среде используем SQLite
            logger.info("Подключение к SQLite в локальной среде...")
            conn = sqlite3.connect('service_bot.db')
            return conn
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        # В случае ошибки подключения к PostgreSQL, используем SQLite
        logger.warning("Использую запасной вариант - SQLite")
        conn = sqlite3.connect('service_bot.db')
        return conn

# Инициализация базы данных
def initialize_database():
    """Инициализация минимальной структуры базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Определяем, используется ли PostgreSQL
    use_postgres = is_postgres()
    
    # Создаем таблицу для минимального тестирования
    if use_postgres:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    
    conn.commit()
    conn.close()
    logger.info("Минимальная структура базы данных инициализирована")

# Функция для добавления тестовой записи в базу данных
def add_test_record(message_text):
    """Добавляет тестовую запись в базу данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgres():
            cursor.execute(
                "INSERT INTO test_table (message) VALUES (%s) RETURNING id",
                (message_text,)
            )
            result = cursor.fetchone()
            record_id = result[0] if result else None
        else:
            cursor.execute(
                "INSERT INTO test_table (message) VALUES (?)",
                (message_text,)
            )
            record_id = cursor.lastrowid
            
        conn.commit()
        logger.info(f"Добавлена тестовая запись: {record_id}")
        return record_id
    except Exception as e:
        logger.error(f"Ошибка при добавлении тестовой записи: {e}")
        return None
    finally:
        conn.close()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Неизвестный"
    
    logger.info(f"Получена команда /start от пользователя {username} (ID: {user_id})")
    
    # Добавляем запись в базу данных для проверки подключения
    try:
        record_id = add_test_record(f"Команда /start от пользователя {username}")
        db_status = f"✅ Запись добавлена в БД (ID: {record_id})" if record_id else "❌ Ошибка записи в БД"
    except Exception as e:
        db_status = f"❌ Ошибка доступа к БД: {e}"
    
    # Отправляем приветственное сообщение
    bot.reply_to(
        message,
        f"Привет, {message.from_user.first_name}! Это минимальная версия бота для тестирования.\n\n"
        f"➡️ Версия telebot: {getattr(telebot, '__version__', 'не определена')}\n"
        f"➡️ Токен: {'Корректный' if TOKEN and ':' in TOKEN else 'Некорректный'} (длина: {len(TOKEN)})\n"
        f"➡️ База данных: {'PostgreSQL' if is_postgres() else 'SQLite'}\n"
        f"➡️ Статус БД: {db_status}\n\n"
        f"Доступные команды:\n"
        f"/start - Показать это сообщение\n"
        f"/ping - Проверить работоспособность бота\n"
        f"/info - Показать системную информацию"
    )

# Обработчик команды /ping
@bot.message_handler(commands=['ping'])
def handle_ping(message):
    """Обработчик команды /ping"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bot.reply_to(
        message,
        f"🟢 Бот работает!\nВремя сервера: {current_time}"
    )

# Обработчик команды /info
@bot.message_handler(commands=['info'])
def handle_info(message):
    """Обработчик команды /info для получения системной информации"""
    # Собираем информацию о системе
    import platform
    
    # Проверяем подключение к базе данных
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_table")
        result = cursor.fetchone()
        records_count = result[0] if result else 0
        conn.close()
        db_status = f"✅ Подключено ({records_count} записей)"
    except Exception as e:
        db_status = f"❌ Ошибка: {str(e)}"
    
    # Собираем информацию о переменных окружения
    env_vars = [
        f"RENDER: {os.environ.get('RENDER', 'не установлена')}",
        f"DATABASE_URL: {'установлена' if os.environ.get('DATABASE_URL') else 'не установлена'}",
        f"TELEGRAM_BOT_TOKEN: {'установлена' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'не установлена'}"
    ]
    
    # Формируем и отправляем сообщение без Markdown-форматирования
    info_message = (
        "📊 Системная информация\n\n"
        f"🔹 Python: {platform.python_version()}\n"
        f"🔹 OS: {platform.system()} {platform.release()}\n"
        f"🔹 Telebot версия: {getattr(telebot, '__version__', 'не определена')}\n"
        f"🔹 База данных: {'PostgreSQL' if is_postgres() else 'SQLite'}\n"
        f"🔹 Статус БД: {db_status}\n\n"
        "🔸 Переменные окружения:\n"
    )
    
    for env_var in env_vars:
        info_message += f"- {env_var}\n"
    
    # Отправляем без parse_mode, чтобы избежать ошибок форматирования
    bot.reply_to(message, info_message)

# Обработчик для всех остальных сообщений
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    """Обработчик всех остальных текстовых сообщений"""
    bot.reply_to(
        message,
        f"Вы отправили: {message.text}\n\n"
        f"Используйте /start для получения списка команд."
    )

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запуск минимальной версии Telegram бота...")
        
        # Инициализируем базу данных
        initialize_database()
        
        # Проверяем токен
        if not TOKEN or ':' not in TOKEN:
            logger.error("Некорректный формат токена бота!")
            return False
        
        # Запускаем бота
        logger.info(f"Запуск бота в режиме polling с токеном длиной {len(TOKEN)}...")
        bot.infinity_polling()
        
        return True
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    """Точка входа при запуске скрипта напрямую"""
    success = main()
    
    if not success:
        logger.error("Бот не запущен из-за ошибок!")
        sys.exit(1)