#!/usr/bin/env python3
"""
Отдельный файл для запуска только Telegram бота без веб-сервера Flask.
Используется как точка входа для workflow 'telegram_bot'.
"""

import os
import sys
import logging
import traceback
import telebot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_bot_token():
    """Получение токена бота из переменных окружения"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token and ':' in token:
        logger.info(f"Используется токен из переменных окружения (длина: {len(token)})")
        return token
    else:
        # Фиксированный токен для использования по умолчанию
        default_token = "8158789441:AAGlPsdPmgTKXtugoa3qlVwb4ee2vW3mL9g"
        logger.info(f"Используется фиксированный токен (длина: {len(default_token)})")
        return default_token

def run_isolated_bot():
    """Запускает изолированную версию бота без зависимостей от Flask"""
    try:
        logger.info("Запуск изолированной версии Telegram бота...")
        
        # Получаем токен бота
        token = get_bot_token()
        
        # Создаем экземпляр бота
        bot = telebot.TeleBot(token)
        
        # Регистрируем базовые обработчики
        @bot.message_handler(commands=['start'])
        def handle_start(message):
            """Обработчик команды /start"""
            user = message.from_user
            bot.reply_to(message, 
                        f"Привет, {user.first_name}! Я бот службы ремонта компьютеров.\n"
                        f"Используйте /help для получения списка команд.")
            logger.info(f"Пользователь {user.first_name} (ID: {user.id}) запустил бота")
        
        @bot.message_handler(commands=['help'])
        def handle_help(message):
            """Обработчик команды /help"""
            help_text = """
            Доступные команды:
            /start - Начать работу с ботом
            /help - Показать это сообщение помощи
            /status - Проверить статус бота
            """
            bot.reply_to(message, help_text)
        
        @bot.message_handler(commands=['status'])
        def handle_status(message):
            """Обработчик команды /status"""
            bot.reply_to(message, "✅ Бот работает в изолированном режиме на порту 5001!\nВеб-сервер работает отдельно на порту 5000.")
        
        @bot.message_handler(content_types=['text'])
        def handle_text(message):
            """Обработчик текстовых сообщений"""
            user = message.from_user
            logger.info(f"Получено сообщение от {user.first_name} (ID: {user.id}): {message.text}")
            
            # Простой ответ на текстовые сообщения
            bot.reply_to(message, f"Вы написали: {message.text}\nЯ работаю в изолированном режиме.")
        
        # Запускаем бота в режиме polling
        logger.info("Запуск бота в режиме polling на порту 5001...")
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1)
        
        return True
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Устанавливаем порт (отличный от порта Flask)
    os.environ['PORT'] = '5001'
    
    # Запускаем бота
    success = run_isolated_bot()
    
    if success:
        logger.info("Telegram бот успешно запущен в изолированном режиме!")
    else:
        logger.error("Не удалось запустить Telegram бота в изолированном режиме!")
        sys.exit(1)