"""
Flask приложение для отображения веб-интерфейса сервиса
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for
from database import initialize_database

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask-приложение
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "service_bot_secret_key")

# Инициализация базы данных
initialize_database()

@app.route('/')
def index():
    """Главная страница"""
    return """
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
                обеспечивая взаимодействие диспетчеров, техников и администраторов.
            </p>
            <div class="features">
                <h3>Возможности:</h3>
                <ul class="list-group mb-4">
                    <li class="list-group-item">✅ Создание и управление заказами</li>
                    <li class="list-group-item">✅ Назначение техников на заказы</li>
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
                        Первый зарегистрированный пользователь автоматически становится администратором.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)