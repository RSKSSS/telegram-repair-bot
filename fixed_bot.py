"""
Обновленный файл для запуска Telegram бота
"""

import os
import telebot
import logging
from shared_state import TOKEN
from database import initialize_database
from logger import get_component_logger

# Настройка логирования
logger = get_component_logger("telegram_bot")
logger.setLevel(logging.INFO)

# Импортируем функции из исправленной версии бота
from bot_fixed import (
    handle_start_command, handle_help_command, handle_new_order_command,
    handle_my_orders_command, handle_my_assigned_orders_command,
    handle_all_orders_command, handle_manage_users_command,
    handle_order_command, handle_callback_query, handle_message
)

def main():
    """
    Основная функция для запуска бота
    """
    try:
        # Инициализируем базу данных
        initialize_database()
        
        # Создаем экземпляр бота
        bot = telebot.TeleBot(TOKEN)
        
        # Регистрация обработчиков команд
        bot.register_message_handler(handle_start_command, commands=['start'])
        bot.register_message_handler(handle_help_command, commands=['help'])
        bot.register_message_handler(handle_new_order_command, commands=['new_order'])
        bot.register_message_handler(handle_my_orders_command, commands=['my_orders'])
        bot.register_message_handler(handle_my_assigned_orders_command, commands=['my_assigned_orders'])
        bot.register_message_handler(handle_all_orders_command, commands=['all_orders'])
        bot.register_message_handler(handle_manage_users_command, commands=['manage_users'])
        
        # Обработчик для команд вида /order_123
        bot.register_message_handler(handle_order_command, regexp=r'^/order_\d+$')
        
        # Регистрация обработчика callback-запросов от inline-кнопок
        bot.register_callback_query_handler(handle_callback_query, func=lambda call: True)
        
        # Регистрация обработчика всех остальных сообщений
        bot.register_message_handler(handle_message, func=lambda message: True, content_types=['text'])
        
        # Запуск бота
        logger.info("Бот успешно запущен и ожидает сообщений")
        bot.infinity_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    main()