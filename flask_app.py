#!/usr/bin/env python
"""
Flask приложение для запуска на порту 5001
"""

import os
import logging
from flask import Flask, render_template, jsonify, request

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем экземпляр Flask
app = Flask(__name__)

# Определяем порт (по умолчанию 5001)
PORT = int(os.environ.get('FLASK_PORT', 5001))

# Главная страница
@app.route('/')
def index():
    """Главная страница"""
    logger.info("Доступ к главной странице")
    return render_template('index.html', title="Сервис ремонта компьютеров")

# API статуса бота
@app.route('/api/bot-status')
def bot_status():
    """Проверка статуса бота"""
    logger.info("Запрос статуса бота")
    return jsonify({
        'status': 'active',
        'version': '1.0',
        'message': 'Бот активен и работает'
    })

# API для получения списка заказов (пример)
@app.route('/api/orders')
def get_orders():
    """Получение списка заказов"""
    logger.info("Запрос списка заказов")
    # Здесь должна быть реальная логика получения заказов из БД
    return jsonify([
        {'id': 1, 'client': 'Иван Иванов', 'problem': 'Не включается компьютер', 'status': 'новый'},
        {'id': 2, 'client': 'Петр Петров', 'problem': 'Медленная работа', 'status': 'в работе'},
    ])

# Обработка ошибок
@app.errorhandler(404)
def not_found(error):
    """Обработка 404 ошибки"""
    logger.warning(f"Страница не найдена: {request.path}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Обработка 500 ошибки"""
    logger.error(f"Серверная ошибка: {error}")
    return render_template('500.html'), 500

# Запуск приложения
if __name__ == '__main__':
    logger.info(f"Запуск Flask на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)