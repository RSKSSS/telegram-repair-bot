#!/usr/bin/env python
"""
Отдельный файл для запуска Flask-приложения на порту, отличном от основного (5000).
Это позволит избежать конфликта с Telegram ботом.
"""

import os
import logging
from app import app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Используем порт 5001 для Flask приложения, чтобы избежать конфликта с ботом
    port = int(os.environ.get("FLASK_PORT", 5001))
    logger.info(f"Запуск Flask-приложения на порту {port}")
    app.run(host='0.0.0.0', port=port)