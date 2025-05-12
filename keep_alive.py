"""
Модуль для поддержания бота активным на Replit
"""
from flask import Flask
from threading import Thread
import logging

# Отключаем логи Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Запускает веб-сервер в отдельном потоке"""
    t = Thread(target=run)
    t.daemon = True
    t.start()