#!/usr/bin/env python
"""
Скрипт диагностики Telegram бота без запуска веб-сервера
"""

import sys
import logging
from bot_diagnostics import run_bot_diagnostics
from database import check_database_connection, get_all_users, get_technicians, get_all_orders, get_problem_templates
from shared_state import TOKEN
from logger import get_component_logger

# Настройка логирования
logger = get_component_logger("bot_diagnostic_no_server")
logger.setLevel(logging.INFO)

def print_diagnostic_results(diagnostics):
    """
    Выводит результаты диагностики в консоль в удобочитаемом формате
    """
    print("\n" + "="*50)
    print(" "*15 + "ДИАГНОСТИКА TELEGRAM БОТА")
    print("="*50)
    
    # Статус подключения к БД
    db_status = "✅ РАБОТАЕТ" if diagnostics["database_connection"] else "❌ ОШИБКА"
    print(f"\n🔧 База данных: {db_status}")
    
    # Статус токена бота
    token_status = "✅ ВАЛИДНЫЙ" if diagnostics["bot_token_valid"] else "❌ НЕВАЛИДНЫЙ"
    print(f"🔑 Токен бота: {token_status} (длина: {len(TOKEN)})")
    
    # Статистика данных
    print("\n📊 СТАТИСТИКА ДАННЫХ:")
    print(f"  • Пользователей: {diagnostics['users_count']}")
    print(f"  • Мастеров: {diagnostics['technicians_count']}")
    print(f"  • Заказов: {diagnostics['orders_count']}")
    print(f"  • Шаблонов проблем: {diagnostics['templates_count']}")
    
    # Ошибки, если есть
    if diagnostics["errors"]:
        print(f"\n⚠️  ОБНАРУЖЕНЫ ОШИБКИ ({len(diagnostics['errors'])}):")
        for i, error in enumerate(diagnostics["errors"], 1):
            print(f"  {i}. {error}")
    else:
        print("\n✅ ОБЩИЙ РЕЗУЛЬТАТ: Ошибок не обнаружено")
    
    print("\n" + "="*50)
    print(" "*15 + "ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("="*50 + "\n")

def run_database_tests():
    """
    Запускает тесты базы данных и выводит подробную информацию
    """
    print("\n--- ТЕСТ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ ---")
    
    try:
        # Проверка соединения
        connection_ok = check_database_connection()
        if connection_ok:
            print("✅ Соединение с базой данных: УСПЕШНО")
        else:
            print("❌ Соединение с базой данных: ОШИБКА")
            return False
        
        # Проверка пользователей
        try:
            users = get_all_users()
            print(f"✅ Получение пользователей: УСПЕШНО (найдено {len(users)})")
            if users:
                print(f"  • Первый пользователь: ID={users[0]['user_id']}, имя={users[0]['first_name']}")
        except Exception as e:
            print(f"❌ Ошибка при получении пользователей: {e}")
        
        # Проверка мастеров
        try:
            technicians = get_technicians()
            print(f"✅ Получение мастеров: УСПЕШНО (найдено {len(technicians)})")
        except Exception as e:
            print(f"❌ Ошибка при получении мастеров: {e}")
        
        # Проверка заказов
        try:
            orders = get_all_orders()
            print(f"✅ Получение заказов: УСПЕШНО (найдено {len(orders)})")
            if orders:
                print(f"  • Первый заказ: ID={orders[0]['order_id']}, статус={orders[0]['status']}")
        except Exception as e:
            print(f"❌ Ошибка при получении заказов: {e}")
        
        # Проверка шаблонов
        try:
            templates = get_problem_templates()
            print(f"✅ Получение шаблонов: УСПЕШНО (найдено {len(templates)})")
        except Exception as e:
            print(f"❌ Ошибка при получении шаблонов: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании базы данных: {e}")
        return False

def check_bot_token():
    """
    Проверяет валидность токена бота
    """
    print("\n--- ПРОВЕРКА ТОКЕНА БОТА ---")
    
    token = TOKEN
    if not token:
        print("❌ Токен бота отсутствует")
        return False
    
    if ":" not in token:
        print(f"❌ Некорректный формат токена (отсутствует двоеточие)")
        return False
    
    print(f"✅ Токен бота валиден (длина: {len(token)})")
    return True

if __name__ == "__main__":
    print("\n📱 ЗАПУСК ДИАГНОСТИКИ TELEGRAM БОТА...\n")
    
    # Проверка подключения к БД
    db_ok = run_database_tests()
    
    # Проверка токена бота
    token_ok = check_bot_token()
    
    # Полная диагностика
    diagnostics = run_bot_diagnostics()
    print_diagnostic_results(diagnostics)
    
    # Итоговый результат
    if db_ok and token_ok and not diagnostics["errors"]:
        print("✅ БОТ ГОТОВ К РАБОТЕ! Все проверки пройдены успешно.")
        sys.exit(0)
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ! Бот может работать некорректно.")
        sys.exit(1)