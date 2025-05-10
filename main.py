#!/usr/bin/env python3
"""
Главный файл для запуска Telegram бота для управления заказами на ремонт компьютеров
"""

import logging
import os
from flask import Flask, render_template, redirect, url_for
from database import initialize_database

# Настройка логирования
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
print("Запуск бота...")

# Импортируем бота из shared_state
from shared_state import bot

# Отключаем AI функции
try:
    import bot
except ImportError as e:
    print(f"Ошибка импорта: {e}")

# AI функции отключены
logger.info("AI функции отключены")

# Создаем Flask-приложение
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "service_bot_secret_key")

@app.route('/')
def index():
    """Главная страница"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Бот для Сервиса Ремонта</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <style>
            body {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                text-align: center;
                padding: 20px;
            }
            .container {
                max-width: 800px;
            }
            .icon {
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            .features {
                text-align: left;
                margin-top: 2rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🤖</div>
            <h1 class="mb-4">Telegram Бот для Сервиса Ремонта</h1>
            <div class="alert alert-success" role="alert">
                <strong>Бот успешно запущен!</strong>
            </div>
            <p class="lead mb-4">
                Этот бот помогает управлять заказами на ремонт компьютерной техники,
                обеспечивая взаимодействие диспетчеров, мастеров и администраторов.
            </p>
            <div class="features">
                <h3>Возможности:</h3>
                <ul class="list-group mb-4">
                    <li class="list-group-item">✅ Создание и управление заказами</li>
                    <li class="list-group-item">✅ Назначение мастеров на заказы</li>
                    <li class="list-group-item">✅ Система подтверждения пользователей (безопасность)</li>
                    <li class="list-group-item">✅ Уведомления о новых заказах и обновлениях</li>
                    <li class="list-group-item">✅ Отслеживание статуса заказов</li>
                </ul>
            </div>
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Как начать использовать бота?</h5>
                    <p class="card-text">
                        Для использования бота найдите его в Telegram и отправьте команду <code>/start</code>.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

def template_folder():
    """Создание папки templates если она не существует"""
    if not os.path.exists('templates'):
        os.makedirs('templates')

def render_template_string(template_string):
    """Отображение шаблона из строки"""
    template_folder()

    # Создаем временный файл шаблона
    with open('templates/temp.html', 'w') as f:
        f.write(template_string)

    return render_template('temp.html')

def main():
    """Запуск бота"""
    logger.info("Инициализация базы данных...")
    initialize_database()

    # Получаем порт из переменной окружения или используем порт по умолчанию
    port = int(os.environ.get('PORT', 5051))
    
    # Проверяем, запущен ли скрипт напрямую через python или в среде Render
    # В среде Render или при запуске через gunicorn, GUNICORN_CMD_ARGS будет определен
    is_direct_run = os.environ.get('GUNICORN_CMD_ARGS') is None and not os.environ.get('RENDER')
    
    # Проверяем наличие токена
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        logger.error("Ошибка: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        if is_direct_run:  # Только выходим, если запущено напрямую
            return
    
    # Запускаем бота в отдельном потоке (и при запуске через gunicorn в Render)
    if is_direct_run or os.environ.get('RENDER'):
        logger.info("Запуск бота сервиса ремонта компьютеров...")
        logger.info("Запуск бота без AI функций")
        
        # Запускаем бота в отдельном потоке
        import threading

        def bot_polling():
            try:
                from shared_state import bot as telebot_instance
                telebot_instance.polling(none_stop=True, interval=0)
            except Exception as e:
                logger.error(f"Ошибка при запуске бота: {e}")

        bot_thread = threading.Thread(target=bot_polling)
        bot_thread.daemon = True
        bot_thread.start()

        logger.info("Бот слушает сообщения...")
    
    if is_direct_run:
        # Запускаем Flask-приложение для веб-интерфейса в режиме разработки
        app.run(host='0.0.0.0', port=port)
    else:
        # В режиме gunicorn не запускаем app.run(), 
        # т.к. gunicorn сам управляет приложением
        logger.info(f"Запущено через gunicorn на порту {port}")
        # Обратите внимание, что в режиме Render бот запускается, 
        # но Flask-приложение управляется gunicorn

if __name__ == "__main__":
    main()