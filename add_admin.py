#!/usr/bin/env python3
"""
Скрипт для добавления пользователя в качестве администратора.
Используйте его для назначения первого администратора.
"""

import sqlite3
import sys
import os
from config import DATABASE_FILE

def add_admin(user_id, first_name="Admin", last_name=None, username=None):
    """
    Добавить пользователя как администратора или повысить существующего пользователя до администратора.
    
    :param user_id: ID пользователя в Telegram
    :param first_name: Имя пользователя (по умолчанию "Admin")
    :param last_name: Фамилия пользователя (опционально)
    :param username: Имя пользователя в Telegram (опционально)
    """
    # Проверяем существование базы данных
    if not os.path.exists(DATABASE_FILE):
        print(f"Ошибка: База данных '{DATABASE_FILE}' не найдена.")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Если пользователь существует, обновляем его роль
            cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', ('admin', user_id))
            print(f"Пользователь с ID {user_id} успешно назначен администратором.")
        else:
            # Если пользователь не существует, создаем нового
            cursor.execute('''
            INSERT INTO users (user_id, first_name, last_name, username, role)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, first_name, last_name, username, 'admin'))
            print(f"Создан новый пользователь с ID {user_id} и ролью администратора.")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        return True
    
    except sqlite3.Error as e:
        print(f"Ошибка SQLite: {e}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return False

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python add_admin.py <user_id> [first_name] [last_name] [username]")
        return
    
    try:
        user_id = int(sys.argv[1])
        first_name = sys.argv[2] if len(sys.argv) > 2 else "Admin"
        last_name = sys.argv[3] if len(sys.argv) > 3 else None
        username = sys.argv[4] if len(sys.argv) > 4 else None
        
        add_admin(user_id, first_name, last_name, username)
    
    except ValueError:
        print("Ошибка: ID пользователя должен быть числом.")

if __name__ == "__main__":
    main()