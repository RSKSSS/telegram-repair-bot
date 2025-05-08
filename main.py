#!/usr/bin/env python3
"""
Главный файл для запуска Telegram бота для управления заказами на ремонт компьютеров
"""

import logging
import os
from flask import Flask, render_template, redirect, url_for
from database import initialize_database
from bot import bot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Create templates folder if it doesn't exist"""
    if not os.path.exists('templates'):
        os.makedirs('templates')

def render_template_string(template_string):
    """Render a template string"""
    template_folder()
    
    # Create a temporary template file
    with open('templates/temp.html', 'w') as f:
        f.write(template_string)
    
    return render_template('temp.html')

def main():
    """Запуск бота"""
    logger.info("Инициализация базы данных...")
    initialize_database()
    
    logger.info("Запуск бота сервиса ремонта компьютеров...")
    
    # Проверяем наличие токена
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        logger.error("Ошибка: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        return
    
    # Проверяем наличие ключа API от OpenAI
    if not os.environ.get('OPENAI_API_KEY'):
        logger.warning("Внимание: Ключ API OpenAI не найден. Функции ИИ-ассистента будут недоступны.")
    else:
        # Регистрируем обработчики AI команд
        try:
            from ai_commands import register_ai_commands
            register_ai_commands(bot)
            logger.info("AI функции успешно зарегистрированы")
        except Exception as e:
            logger.error(f"Ошибка при регистрации AI функций: {e}")
    
    # Запускаем бота в отдельном потоке
    import threading
    bot_thread = threading.Thread(target=bot.infinity_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    logger.info("Бот слушает сообщения...")
    
    # Запускаем Flask-приложение для веб-интерфейса
    app.run(host='0.0.0.0', port=5051)

if __name__ == "__main__":
    main()