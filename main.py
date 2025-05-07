#!/usr/bin/env python3
"""
Главный файл для запуска Telegram бота для управления заказами на ремонт компьютеров
"""

import logging
import os
from database import initialize_database
from bot import bot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    logger.info("Инициализация базы данных...")
    initialize_database()
    
    logger.info("Запуск бота сервиса ремонта компьютеров...")
    
    # Проверяем наличие токена
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        logger.error("Ошибка: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        return
    
    # Запускаем бота
    logger.info("Бот слушает сообщения...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()