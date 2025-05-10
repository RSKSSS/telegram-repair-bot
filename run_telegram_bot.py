#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота без Flask сервера
"""

import os
import logging
import traceback
from telebot import TeleBot, types
from database import initialize_database, check_database_connection
from shared_state import bot, TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_bot_token():
    """Проверяет валидность токена бота"""
    token = TOKEN
    if not token:
        logger.error("ОШИБКА: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        return False
    if ':' not in token:
        logger.error(f"ОШИБКА: Невалидный формат токена. Текущая длина: {len(token)}")
        return False
    
    logger.info(f"Токен Telegram бота найден, длина: {len(token)} символов, формат корректный")
    return True

# Минимальные обработчики для тестирования работы бота
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start"""
    bot.reply_to(message, "Привет! Сервисный бот запущен и работает!")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Обработчик команды /help"""
    bot.reply_to(message, "Это тестовая версия бота для проверки работоспособности.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик текстовых сообщений"""
    bot.reply_to(message, f"Вы отправили: {message.text}")

def main():
    """Главная функция запуска бота"""
    try:
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        initialize_database()
        logger.info("База данных инициализирована")
        
        # Проверяем подключение к базе данных
        db_connection = check_database_connection()
        if not db_connection:
            logger.error("ОШИБКА: Не удалось подключиться к базе данных! Бот не будет запущен.")
            return False
        
        # Проверяем токен бота
        if not check_bot_token():
            return False
        
        # Запускаем бота
        logger.info("Запуск бота в режиме polling...")
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
        logger.info("Бот успешно запущен и работает!")
    else:
        logger.error("Не удалось запустить бота из-за ошибок.")