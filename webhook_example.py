import os
import telebot
from flask import Flask, request

# Основные переменные
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://ваш-проект.onrender.com')

# Инициализация бота и Flask-приложения
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Обработчик вебхуков
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK'

# Установка вебхука при запуске
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + '/' + BOT_TOKEN)
    return f'Webhook установлен на {WEBHOOK_URL}'

# Простой маршрут для проверки работоспособности
@app.route('/', methods=['GET'])
def index():
    return 'Бот запущен и работает'

# Ваши обработчики команд бота здесь
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Привет! Я бот сервиса ремонта компьютеров.")

# Основной блок запуска
if __name__ == '__main__':
    # Определяем порт для запуска
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем Flask-приложение
    app.run(host='0.0.0.0', port=port)