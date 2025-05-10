#!/usr/bin/env python3
"""
Главный файл для запуска Telegram бота для управления заказами на ремонт компьютеров
"""

import logging
import os
import datetime
from flask import Flask, render_template, redirect, url_for, jsonify
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

@app.route('/healthcheck')
def healthcheck():
    """Эндпоинт для проверки работоспособности приложения"""
    try:
        # Проверяем состояние базы данных
        from database import check_database_connection
        db_status = "ok" if check_database_connection() else "error"
        
        # Проверяем состояние бота (если возможно)
        bot_status = "unknown"
        bot_name = "Unknown"
        try:
            from shared_state import bot as telebot_instance
            bot_info = telebot_instance.get_me()
            if bot_info:
                bot_status = "ok"
                # Обработка ответа, который может быть как объектом, так и словарем
                if hasattr(bot_info, 'first_name'):
                    bot_name = bot_info.first_name
                elif isinstance(bot_info, dict) and 'first_name' in bot_info:
                    bot_name = bot_info['first_name']
                elif isinstance(bot_info, dict) and 'username' in bot_info:
                    bot_name = bot_info['username']
                else:
                    bot_name = "Bot Active"
        except Exception as bot_err:
            logger.warning(f"Bot check error: {bot_err}")
            bot_status = "error"
        
        # Возвращаем ответ (всегда 200, чтобы UptimeRobot считал сервис работающим)
        return {
            "status": "ok",
            "server": "running",
            "database": db_status,
            "bot": bot_status,
            "bot_name": bot_name,
            "timestamp": str(datetime.datetime.now())
        }, 200
    except Exception as e:
        logger.error(f"Healthcheck error: {e}")
        # Даже в случае ошибки возвращаем 200 для UptimeRobot, 
        # но с информацией об ошибке
        return {
            "status": "warning",
            "server": "running",
            "error": str(e),
            "timestamp": str(datetime.datetime.now())
        }, 200

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

def bot_polling():
    """Функция для запуска бота в режиме polling"""
    try:
        from shared_state import bot as telebot_instance
        
        # Проверим валидность токена перед запуском
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token or ':' not in token:
            logger.error(f"Ошибка: Невалидный формат токена. Токен должен содержать двоеточие (:). Текущая длина: {len(token) if token else 0}")
            print(f"Ошибка: Невалидный формат токена. Токен должен содержать двоеточие (:). Текущая длина: {len(token) if token else 0}")
            return
            
        # Пробуем получить информацию о боте перед запуском polling
        try:
            bot_info = telebot_instance.get_me()
            if isinstance(bot_info, dict) and 'username' in bot_info:
                logger.info(f"Бот успешно подключен. Имя бота: @{bot_info['username']}")
            elif hasattr(bot_info, 'username') and bot_info.username:
                logger.info(f"Бот успешно подключен. Имя бота: @{bot_info.username}")
            else:
                logger.info(f"Бот подключен. Детали: {str(bot_info)}")
        except Exception as info_err:
            logger.warning(f"Не удалось получить информацию о боте: {info_err}")
        
        # Запускаем polling с обработкой ошибок
        # Вместо обычного polling используем infinity_polling, который лучше обрабатывает ошибки
        telebot_instance.infinity_polling(interval=1)
    except Exception as e:
        error_message = f"Ошибка при запуске бота: {e}"
        logger.error(error_message)
        print(error_message)
        
        # Добавляем расширенную информацию об ошибке
        if "Unauthorized" in str(e):
            extra_info = """
            Ошибка 401 Unauthorized означает, что токен бота недействителен.
            Убедитесь, что:
            1. Токен скопирован полностью и без лишних символов
            2. Токен действительно получен от @BotFather
            3. Токен не был отозван (можно проверить в списке ботов в @BotFather)
            """
            logger.error(extra_info)
            print(extra_info)

def main():
    """Запуск бота"""
    logger.info("Инициализация базы данных...")
    initialize_database()

    # Получаем порт из переменной окружения или используем порт по умолчанию
    # На Render порт задается через переменную PORT
    port = int(os.environ.get('PORT', 5051))
    logger.info(f"Используем порт: {port}")
    
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
        
        # Запускаем бота через функцию bot_polling
        bot_thread = threading.Thread(target=bot_polling)
        bot_thread.daemon = True
        bot_thread.start()

        logger.info("Бот слушает сообщения...")
    
    if is_direct_run:
        # Запускаем Flask-приложение для веб-интерфейса в режиме разработки
        app.run(host='0.0.0.0', port=port)
    elif os.environ.get('RENDER'):
        # В режиме Render явно запускаем приложение на указанном порту
        logger.info(f"Запуск в режиме Render на порту {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        # В режиме gunicorn не запускаем app.run(), 
        # т.к. gunicorn сам управляет приложением
        logger.info(f"Запущено через gunicorn на порту {port}")
        # Обратите внимание, что в режиме Render бот запускается, 
        # но Flask-приложение управляется gunicorn

if __name__ == "__main__":
    main()