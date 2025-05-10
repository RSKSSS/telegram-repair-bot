#!/usr/bin/env python3
"""
Файл настройки переменных окружения для запуска бота
"""

import os

# Устанавливаем переменную окружения SKIP_BOT_START для workflow "Start application",
# чтобы избежать конфликта с запуском бота из workflow "telegram_bot"
os.environ['SKIP_BOT_START'] = '1'

# Устанавливаем переменную окружения с токеном Telegram бота
os.environ['TELEGRAM_BOT_TOKEN'] = '8158789441:AAGlPsdPmgTKXtugoa3qlVwb4ee2vW3mL9g'

# Устанавливаем переменные окружения для подключения к PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://bot_db_utg6_user:OYRUr0ikJTC6SQgWKV5sL15F9sDZcpt8@dpg-d0fa5015pdvs73c2d0f0-a/bot_db_utg6'
os.environ['PGDATABASE'] = 'bot_db_utg6'
os.environ['PGHOST'] = 'dpg-d0fa5015pdvs73c2d0f0-a'
os.environ['PGPORT'] = '5432'
os.environ['PGUSER'] = 'bot_db_utg6_user'
os.environ['PGPASSWORD'] = 'OYRUr0ikJTC6SQgWKV5sL15F9sDZcpt8'