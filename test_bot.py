#!/usr/bin/env python
"""
Простой скрипт для тестирования бота без конфликта портов
"""

import telebot
from shared_state import TOKEN

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

# Регистрируем простые обработчики
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.reply_to(message, "Тестовый режим бота активен. Бот работает!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Получено сообщение: {message.text}")

if __name__ == "__main__":
    print("Запуск тестового режима бота...")
    print(f"Используется токен длиной: {len(TOKEN)} символов")
    bot.infinity_polling()
    print("Бот остановлен")