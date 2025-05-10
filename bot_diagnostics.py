"""
Модуль для диагностики и запуска Telegram бота
"""

import os
import sys
import logging
import telebot
from telebot.types import Message
from database import (
    check_database_connection, 
    get_all_users, 
    get_problem_templates,
    get_technicians,
    get_all_orders
)
from shared_state import bot, TOKEN
from logger import get_component_logger

# Настройка логирования
logger = get_component_logger("bot_diagnostics")
logger.setLevel(logging.INFO)

def run_bot_diagnostics():
    """
    Запуск полной диагностики бота и всех его компонентов
    Возвращает словарь с результатами диагностики
    """
    logger.info("Запуск полной диагностики бота...")
    
    diagnostics_results = {
        "database_connection": False,
        "bot_token_valid": False,
        "users_count": 0,
        "templates_count": 0,
        "technicians_count": 0,
        "orders_count": 0,
        "errors": []
    }
    
    # 1. Проверка подключения к базе данных
    try:
        db_connection = check_database_connection()
        diagnostics_results["database_connection"] = db_connection
        if db_connection:
            logger.info("✅ Подключение к базе данных: успешно")
        else:
            logger.error("❌ Подключение к базе данных: ошибка")
            diagnostics_results["errors"].append("Не удалось подключиться к базе данных")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке подключения к базе данных: {e}")
        diagnostics_results["errors"].append(f"Ошибка при проверке БД: {str(e)}")
    
    # 2. Проверка токена бота
    try:
        token = TOKEN
        if token and ":" in token:
            diagnostics_results["bot_token_valid"] = True
            logger.info(f"✅ Токен бота валиден (длина: {len(token)})")
        else:
            logger.error(f"❌ Токен бота невалиден или отсутствует (длина: {len(token) if token else 0})")
            diagnostics_results["errors"].append("Некорректный токен бота")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке токена бота: {e}")
        diagnostics_results["errors"].append(f"Ошибка проверки токена: {str(e)}")
    
    # 3. Проверка доступа к данным пользователей
    try:
        users = get_all_users()
        diagnostics_results["users_count"] = len(users)
        logger.info(f"✅ Количество пользователей в системе: {len(users)}")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка пользователей: {e}")
        diagnostics_results["errors"].append(f"Ошибка получения пользователей: {str(e)}")
    
    # 4. Проверка шаблонов проблем
    try:
        templates = get_problem_templates()
        diagnostics_results["templates_count"] = len(templates)
        logger.info(f"✅ Количество шаблонов проблем: {len(templates)}")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении шаблонов проблем: {e}")
        diagnostics_results["errors"].append(f"Ошибка получения шаблонов: {str(e)}")
    
    # 5. Проверка доступа к данным мастеров
    try:
        technicians = get_technicians()
        diagnostics_results["technicians_count"] = len(technicians)
        logger.info(f"✅ Количество мастеров в системе: {len(technicians)}")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка мастеров: {e}")
        diagnostics_results["errors"].append(f"Ошибка получения мастеров: {str(e)}")
    
    # 6. Проверка доступа к данным заказов
    try:
        orders = get_all_orders()
        diagnostics_results["orders_count"] = len(orders)
        logger.info(f"✅ Количество заказов в системе: {len(orders)}")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка заказов: {e}")
        diagnostics_results["errors"].append(f"Ошибка получения заказов: {str(e)}")
    
    # Вывод общего результата диагностики
    if not diagnostics_results["errors"]:
        logger.info("✅ Диагностика завершена успешно! Ошибок не обнаружено.")
    else:
        logger.error(f"❌ Диагностика завершена с ошибками: {len(diagnostics_results['errors'])} ошибок")
        for i, error in enumerate(diagnostics_results["errors"], 1):
            logger.error(f"  Ошибка {i}: {error}")
    
    return diagnostics_results

def bot_polling():
    """
    Функция для запуска бота в режиме polling
    Используется render_app.py для запуска бота в отдельном потоке
    """
    try:
        # Импортируем и используем start_bot вместо прямого запуска
        from start_bot import start_bot
        logger.info("Запуск бота через функцию start_bot()...")
        
        # Проверяем состояние бота через диагностику
        diagnostics = run_bot_diagnostics()
        
        if not diagnostics["bot_token_valid"]:
            logger.error("❌ Невозможно запустить бота: невалидный токен")
            return
        
        if not diagnostics["database_connection"]:
            logger.error("❌ Невозможно запустить бота: проблемы с подключением к БД")
            return
        
        # Запускаем бота, используя функцию из start_bot.py
        # которая правильно настраивает все обработчики
        start_bot()
        logger.info("Бот остановлен")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        # Используем traceback для получения полного стека ошибки
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Запускаем диагностику для проверки состояния системы
    diagnostics = run_bot_diagnostics()
    
    # Если диагностика успешна, запускаем бота
    if not diagnostics["errors"]:
        bot_polling()
    else:
        logger.error(f"❌ Бот не запущен из-за ошибок диагностики: {len(diagnostics['errors'])} ошибок")
        sys.exit(1)