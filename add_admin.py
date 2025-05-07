#!/usr/bin/env python3
"""
Скрипт для добавления пользователя в качестве администратора.
Используйте его для назначения первого администратора.
"""

import logging
import sys
from database import get_connection, get_user, save_user, initialize_database

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_admin(user_id, first_name="Admin", last_name=None, username=None):
    """
    Добавить пользователя как администратора или повысить существующего пользователя до администратора.
    
    :param user_id: ID пользователя в Telegram
    :param first_name: Имя пользователя (по умолчанию "Admin")
    :param last_name: Фамилия пользователя (опционально)
    :param username: Имя пользователя в Telegram (опционально)
    """
    initialize_database()
    
    # Проверяем, существует ли пользователь
    user = get_user(user_id)
    
    if user:
        # Обновляем роль существующего пользователя
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET role = 'admin', is_approved = TRUE WHERE user_id = %s",
                (user_id,)
            )
            conn.commit()
            logger.info(f"Пользователь (ID: {user_id}) повышен до администратора.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка при обновлении пользователя: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        # Создаем нового пользователя с ролью администратора
        save_user(user_id, first_name, last_name, username, 'admin', True)
        logger.info(f"Создан новый администратор (ID: {user_id}).")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python add_admin.py <telegram_id> [first_name] [last_name] [username]")
        print("Пример: python add_admin.py 123456789 John Doe johndoe")
        return
    
    user_id = int(sys.argv[1])
    first_name = sys.argv[2] if len(sys.argv) > 2 else "Admin"
    last_name = sys.argv[3] if len(sys.argv) > 3 else None
    username = sys.argv[4] if len(sys.argv) > 4 else None
    
    add_admin(user_id, first_name, last_name, username)
    
if __name__ == "__main__":
    main()