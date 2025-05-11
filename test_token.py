#!/usr/bin/env python
"""
Скрипт для тестирования токена Telegram бота.
Просто проверяет, может ли бот подключиться к API Telegram.
"""

import os
import sys
import logging
import telebot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Тестирование токена"""
    # Получаем токен из переменной окружения
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения!")
        return False
    
    logger.info(f"Токен получен (длина: {len(token)})")
    logger.info(f"Первые 5 символов: {token[:5]}")
    logger.info(f"Последние 5 символов: {token[-5:]}")
    
    try:
        # Создаем экземпляр бота
        bot = telebot.TeleBot(token)
        
        # Проверяем соединение, получая информацию о боте
        bot_info = bot.get_me()
        
        logger.info(f"Успешное подключение! Информация о боте:")
        logger.info(f"ID: {bot_info.id}")
        logger.info(f"Имя: {bot_info.first_name}")
        logger.info(f"Username: @{bot_info.username}")
        
        return True
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Ошибка API Telegram: {e}")
        if "401" in str(e):
            logger.error("Ошибка авторизации (401) - токен недействителен или отозван.")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Тест успешно пройден! Токен действителен.")
        sys.exit(0)
    else:
        logger.error("Тест провален. Проверьте токен и соединение.")
        sys.exit(1)