#!/usr/bin/env python3
"""
Файл для запуска только Telegram бота без Flask сервера
Этот файл полностью независим от Flask и не импортирует flask-зависимые модули
"""

import os
import sys
import logging
import telebot
import traceback
from database import initialize_database, check_database_connection

# Настройка логирования
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменной окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if TOKEN is None or ':' not in TOKEN:
    TOKEN = "8158789441:AAGlPsdPmgTKXtugoa3qlVwb4ee2vW3mL9g"  # Фиксированный токен
    logger.info(f"Загружен фиксированный токен длиной: {len(TOKEN)} символов")
    print(f"Загружен фиксированный токен длиной: {len(TOKEN)} символов")
else:
    logger.info(f"Загружен токен из переменной окружения длиной: {len(TOKEN)} символов")
    print(f"Загружен токен из переменной окружения длиной: {len(TOKEN)} символов")

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

def check_bot_token():
    """Проверяет валидность токена бота"""
    if not TOKEN:
        logger.error("ОШИБКА: Токен Telegram бота не найден.")
        return False
    if ':' not in TOKEN:
        logger.error(f"ОШИБКА: Невалидный формат токена. Текущая длина: {len(TOKEN)}")
        return False
    
    logger.info(f"Токен Telegram бота найден, длина: {len(TOKEN)} символов")
    return True

# Минимальные обработчики для тестирования работы бота
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    bot.reply_to(message, "Привет! Сервисный бот запущен и работает!")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Обработчик команды /help"""
    help_text = """
    Это минимальная версия бота для проверки работоспособности.
    
    Доступные команды:
    /start - Начать работу с ботом
    /help - Показать это сообщение помощи
    """
    bot.reply_to(message, help_text)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик текстовых сообщений"""
    bot.reply_to(message, f"Вы отправили: {message.text}")

def main():
    """Основная функция запуска бота"""
    try:
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        initialize_database()
        logger.info("База данных инициализирована")
        
        # Проверяем подключение к базе данных
        db_connection = check_database_connection()
        if not db_connection:
            logger.error("ОШИБКА: Не удалось подключиться к базе данных! Использую SQLite.")
        
        # Проверяем токен бота
        if not check_bot_token():
            return False
        
        # Запускаем бота (независимо от Flask)
        logger.info("Запуск Telegram бота в режиме polling...")
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1)
        
        return True
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Telegram бот успешно запущен!")
    else:
        logger.error("Не удалось запустить Telegram бота!")
        sys.exit(1)