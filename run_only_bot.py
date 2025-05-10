#!/usr/bin/env python
"""
Скрипт для запуска только Telegram бота без веб-сервера
Этот скрипт используется в рабочем процессе "telegram_bot" для запуска бота
без конфликта портов с основным Flask-приложением.
"""

import sys
from start_bot import start_bot

if __name__ == "__main__":
    print("Запуск только Telegram бота без веб-сервера...")
    
    # Запускаем бота, используя функцию из start_bot.py
    success = start_bot()
    
    if not success:
        print("Ошибка при запуске бота!")
        sys.exit(1)