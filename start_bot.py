#!/usr/bin/env python
"""
Скрипт для запуска Telegram бота с корректной регистрацией всех обработчиков сообщений
"""

import os
import sys
import logging
import telebot
from telebot.types import Message, CallbackQuery

from database import initialize_database
from logger import get_component_logger
from shared_state import bot, TOKEN, init_bot

# Настройка логирования
logger = get_component_logger("bot_starter")
logger.setLevel(logging.INFO)

# Импортируем все нужные обработчики
from bot_fixed import (
    handle_start_command, handle_help_command, handle_new_order_command,
    handle_my_orders_command, handle_my_assigned_orders_command,
    handle_all_orders_command, handle_manage_users_command,
    handle_order_command, handle_callback_query, handle_message
)

def register_all_handlers(bot_instance):
    """
    Регистрирует все обработчики сообщений для бота
    """
    logger.info("Регистрация обработчиков сообщений...")
    
    # Основные команды
    bot_instance.register_message_handler(handle_start_command, commands=['start'])
    bot_instance.register_message_handler(handle_help_command, commands=['help'])
    bot_instance.register_message_handler(handle_new_order_command, commands=['new_order'])
    bot_instance.register_message_handler(handle_my_orders_command, commands=['my_orders'])
    bot_instance.register_message_handler(handle_my_assigned_orders_command, commands=['my_assigned_orders'])
    bot_instance.register_message_handler(handle_all_orders_command, commands=['all_orders'])
    bot_instance.register_message_handler(handle_manage_users_command, commands=['manage_users'])
    
    # Обработчик для команд вида /order_123
    bot_instance.register_message_handler(handle_order_command, regexp=r'^/order_\d+$')
    
    # Регистрация обработчика для команды диагностики бота
    bot_instance.register_message_handler(handle_diagnostic_command, commands=['diagnostics'])
    
    # Регистрация обработчика callback-запросов от inline-кнопок
    bot_instance.register_callback_query_handler(handle_callback_query, func=lambda call: True)
    
    # Регистрация обработчика всех остальных сообщений (должен быть последним)
    bot_instance.register_message_handler(handle_message, func=lambda message: True, content_types=['text'])
    
    logger.info("Все обработчики зарегистрированы")
    return bot_instance

def handle_diagnostic_command(message: Message):
    """
    Обработчик команды /diagnostics - запускает полную диагностику бота
    """
    from bot_diagnostics import run_bot_diagnostics
    from utils import is_admin

    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    
    if is_admin(user_id):
        bot.send_message(message.chat.id, "🔄 Запуск диагностики бота...")
        
        # Запуск диагностики
        diagnostics = run_bot_diagnostics()
        
        # Формируем отчет
        report = "📊 *Отчет о диагностике бота* 📊\n\n"
        
        # Статус подключения к БД
        db_status = "✅ Работает" if diagnostics["database_connection"] else "❌ Ошибка"
        report += f"*База данных*: {db_status}\n"
        
        # Статус токена бота
        token_status = "✅ Валидный" if diagnostics["bot_token_valid"] else "❌ Невалидный"
        report += f"*Токен бота*: {token_status}\n\n"
        
        # Статистика данных
        report += f"*Пользователей*: {diagnostics['users_count']}\n"
        report += f"*Мастеров*: {diagnostics['technicians_count']}\n"
        report += f"*Заказов*: {diagnostics['orders_count']}\n"
        report += f"*Шаблонов проблем*: {diagnostics['templates_count']}\n\n"
        
        # Ошибки, если есть
        if diagnostics["errors"]:
            report += f"*Обнаружены ошибки ({len(diagnostics['errors'])})* ⚠️:\n"
            for i, error in enumerate(diagnostics["errors"], 1):
                report += f"{i}. {error}\n"
        else:
            report += "*Ошибок не обнаружено* ✅"
        
        bot.send_message(
            message.chat.id,
            report,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "❌ У вас нет прав для запуска диагностики.")

def test_message_handler(message: Message):
    """
    Тестовый обработчик для проверки работы бота
    """
    logger.info(f"Получено тестовое сообщение: {message.text}")
    bot.reply_to(message, f"Бот работает! Получено сообщение: {message.text}")

def start_bot():
    """
    Запускает бота и регистрирует все обработчики
    """
    try:
        logger.info("Запуск Telegram бота...")
        
        # Инициализация базы данных
        logger.info("Инициализация базы данных...")
        initialize_database()
        logger.info("База данных инициализирована")
        
        # Проверка токена
        if not TOKEN or ':' not in TOKEN:
            logger.error(f"Невалидный токен бота: {TOKEN}")
            return False
        
        # Используем глобальный экземпляр бота из shared_state
        logger.info(f"Используем глобальный экземпляр бота с токеном длиной {len(TOKEN)}")
        
        # Регистрируем все обработчики
        register_all_handlers(bot)
        
        # Добавляем тестовый обработчик
        bot.register_message_handler(test_message_handler, commands=['test'])
        
        # Запускаем бота в режиме polling
        logger.info("Запуск бота в режиме polling...")
        bot.infinity_polling()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Запуск Telegram бота...")
    
    # Запускаем бота
    success = start_bot()
    
    if not success:
        print("Ошибка при запуске бота!")
        sys.exit(1)