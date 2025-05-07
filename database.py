"""
Модуль для работы с базой данных PostgreSQL
"""

import logging
import os
import datetime
import psycopg2
from psycopg2 import sql
from typing import Optional, List, Dict

from models import User, Order, Assignment

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Получение соединения с PostgreSQL базой данных"""
    return psycopg2.connect(
        os.environ.get('DATABASE_URL')
    )

def initialize_database():
    """Инициализация базы данных - создание таблиц если они не существуют"""
    logger.info("Инициализация базы данных...")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Создаем таблицу пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                username TEXT,
                role TEXT NOT NULL DEFAULT 'technician',
                is_approved BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем таблицу заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                client_phone TEXT NOT NULL,
                client_name TEXT NOT NULL,
                client_address TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                dispatcher_id BIGINT REFERENCES users(user_id),
                status TEXT NOT NULL DEFAULT 'new',
                service_cost NUMERIC,
                service_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем таблицу назначений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id),
                technician_id BIGINT REFERENCES users(user_id),
                assigned_by BIGINT REFERENCES users(user_id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем таблицу для хранения состояний пользователей в боте
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id BIGINT PRIMARY KEY,
                state TEXT NOT NULL,
                order_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("Инициализация базы данных успешно завершена.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        cursor.close()
        conn.close()

def save_user(user_id, first_name, last_name=None, username=None, role='technician', is_approved=False):
    """Сохранение информации о пользователе в базу данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже пользователь
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Обновляем существующего пользователя
            cursor.execute(
                "UPDATE users SET first_name = %s, last_name = %s, username = %s WHERE user_id = %s",
                (first_name, last_name, username, user_id)
            )
        else:
            # Проверяем, есть ли уже администратор в системе
            if role == 'technician':
                cursor.execute("SELECT user_id FROM users WHERE role = 'admin'")
                existing_admin = cursor.fetchone()
                
                # Если нет админов, первый пользователь становится админом
                if not existing_admin:
                    role = 'admin'
                    is_approved = True
            
            # Вставляем нового пользователя
            cursor.execute(
                "INSERT INTO users (user_id, first_name, last_name, username, role, is_approved) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, first_name, last_name, username, role, is_approved)
            )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при сохранении пользователя: {e}")
    finally:
        cursor.close()
        conn.close()

def get_user(user_id):
    """Получение информации о пользователе из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return None
            
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        # Создаем словарь с данными пользователя
        user_dict = {column_names[i]: user_data[i] for i in range(len(column_names))}
        
        return User.from_dict(user_dict)
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_role(user_id):
    """Получение роли пользователя из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        role = cursor.fetchone()
        
        return role[0] if role else None
    except Exception as e:
        logger.error(f"Ошибка при получении роли пользователя: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_users():
    """Получение всех пользователей из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        users = []
        for user_data in users_data:
            # Создаем словарь с данными пользователя
            user_dict = {column_names[i]: user_data[i] for i in range(len(column_names))}
            users.append(User.from_dict(user_dict))
        
        return users
    except Exception as e:
        logger.error(f"Ошибка при получении всех пользователей: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_technicians():
    """Получение всех мастеров из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE role = 'technician' AND is_approved = TRUE ORDER BY created_at DESC")
        users_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        technicians = []
        for user_data in users_data:
            # Создаем словарь с данными пользователя
            user_dict = {column_names[i]: user_data[i] for i in range(len(column_names))}
            technicians.append(User.from_dict(user_dict))
        
        return technicians
    except Exception as e:
        logger.error(f"Ошибка при получении мастеров: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_user_role(user_id, role):
    """Обновление роли пользователя в базе данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET role = %s WHERE user_id = %s", (role, user_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при обновлении роли пользователя: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def approve_user(user_id):
    """Подтверждение пользователя администратором"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET is_approved = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при подтверждении пользователя: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def reject_user(user_id):
    """Отклонение пользователя администратором"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при отклонении пользователя: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def is_user_approved(user_id):
    """Проверка, подтвержден ли пользователь администратором"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT is_approved FROM users WHERE user_id = %s", (user_id,))
        approved = cursor.fetchone()
        
        return approved[0] if approved else False
    except Exception as e:
        logger.error(f"Ошибка при проверке подтверждения пользователя: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_unapproved_users():
    """Получение всех неподтвержденных пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE is_approved = FALSE ORDER BY created_at DESC")
        users_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        users = []
        for user_data in users_data:
            # Создаем словарь с данными пользователя
            user_dict = {column_names[i]: user_data[i] for i in range(len(column_names))}
            users.append(User.from_dict(user_dict))
        
        return users
    except Exception as e:
        logger.error(f"Ошибка при получении неподтвержденных пользователей: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def save_order(dispatcher_id, client_phone, client_name, client_address, problem_description):
    """Сохранение заказа в базу данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Вставляем новый заказ
        cursor.execute(
            "INSERT INTO orders (dispatcher_id, client_phone, client_name, client_address, problem_description) VALUES (%s, %s, %s, %s, %s) RETURNING order_id",
            (dispatcher_id, client_phone, client_name, client_address, problem_description)
        )
        order_id = cursor.fetchone()[0]
        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при сохранении заказа: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_order(order_id, status=None, service_cost=None, service_description=None):
    """Обновление заказа в базе данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        update_values = []
        update_fields = []
        
        if status is not None:
            update_fields.append("status = %s")
            update_values.append(status)
        
        if service_cost is not None:
            update_fields.append("service_cost = %s")
            update_values.append(service_cost)
        
        if service_description is not None:
            update_fields.append("service_description = %s")
            update_values.append(service_description)
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_query = f"UPDATE orders SET {', '.join(update_fields)} WHERE order_id = %s"
            cursor.execute(update_query, update_values + [order_id])
            conn.commit()
            return True
        
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при обновлении заказа: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_order(order_id):
    """Получение заказа из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем данные заказа с информацией о диспетчере
        cursor.execute("""
            SELECT o.*, u.first_name, u.last_name
            FROM orders o
            LEFT JOIN users u ON o.dispatcher_id = u.user_id
            WHERE o.order_id = %s
        """, (order_id,))
        order_data = cursor.fetchone()
        
        if not order_data:
            return None
            
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        # Создаем словарь с данными заказа
        order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
        
        # Получаем мастеров, назначенных на заказ
        cursor.execute("""
            SELECT a.*, u.first_name, u.last_name, u.username
            FROM assignments a
            JOIN users u ON a.technician_id = u.user_id
            WHERE a.order_id = %s
        """, (order_id,))
        
        technicians_data = cursor.fetchall()
        
        # Получаем имена столбцов для мастеров
        tech_column_names = [desc[0] for desc in cursor.description]
        
        technicians = []
        for tech_data in technicians_data:
            # Создаем словарь с данными мастера
            tech_dict = {tech_column_names[i]: tech_data[i] for i in range(len(tech_column_names))}
            technicians.append(tech_dict)
        
        order_dict['technicians'] = technicians
        order_dict['dispatcher_first_name'] = order_dict.get('first_name')
        order_dict['dispatcher_last_name'] = order_dict.get('last_name')
        
        return Order.from_dict(order_dict)
    except Exception as e:
        logger.error(f"Ошибка при получении заказа: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_orders_by_user(user_id):
    """Получение всех заказов созданных пользователем (для диспетчера)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT o.*, u.first_name, u.last_name
            FROM orders o
            LEFT JOIN users u ON o.dispatcher_id = u.user_id
            WHERE o.dispatcher_id = %s
            ORDER BY o.created_at DESC
        """, (user_id,))
        orders_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        orders = []
        for order_data in orders_data:
            # Создаем словарь с данными заказа
            order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
            
            # Получаем мастеров, назначенных на заказ
            cursor.execute("""
                SELECT a.*, u.first_name, u.last_name, u.username
                FROM assignments a
                JOIN users u ON a.technician_id = u.user_id
                WHERE a.order_id = %s
            """, (order_dict['order_id'],))
            
            technicians_data = cursor.fetchall()
            
            # Получаем имена столбцов для мастеров
            tech_column_names = [desc[0] for desc in cursor.description]
            
            technicians = []
            for tech_data in technicians_data:
                # Создаем словарь с данными мастера
                tech_dict = {tech_column_names[i]: tech_data[i] for i in range(len(tech_column_names))}
                technicians.append(tech_dict)
            
            order_dict['technicians'] = technicians
            order_dict['dispatcher_first_name'] = order_dict.get('first_name')
            order_dict['dispatcher_last_name'] = order_dict.get('last_name')
            
            orders.append(Order.from_dict(order_dict))
        
        return orders
    except Exception as e:
        logger.error(f"Ошибка при получении заказов пользователя: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_assigned_orders(technician_id):
    """Получение заказов, назначенных мастеру"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT o.*, u.first_name, u.last_name
            FROM orders o
            LEFT JOIN users u ON o.dispatcher_id = u.user_id
            JOIN assignments a ON o.order_id = a.order_id
            WHERE a.technician_id = %s
            ORDER BY o.created_at DESC
        """, (technician_id,))
        orders_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        orders = []
        for order_data in orders_data:
            # Создаем словарь с данными заказа
            order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
            
            # Получаем мастеров, назначенных на заказ
            cursor.execute("""
                SELECT a.*, u.first_name, u.last_name, u.username
                FROM assignments a
                JOIN users u ON a.technician_id = u.user_id
                WHERE a.order_id = %s
            """, (order_dict['order_id'],))
            
            technicians_data = cursor.fetchall()
            
            # Получаем имена столбцов для мастеров
            tech_column_names = [desc[0] for desc in cursor.description]
            
            technicians = []
            for tech_data in technicians_data:
                # Создаем словарь с данными мастера
                tech_dict = {tech_column_names[i]: tech_data[i] for i in range(len(tech_column_names))}
                technicians.append(tech_dict)
            
            order_dict['technicians'] = technicians
            order_dict['dispatcher_first_name'] = order_dict.get('first_name')
            order_dict['dispatcher_last_name'] = order_dict.get('last_name')
            
            orders.append(Order.from_dict(order_dict))
        
        return orders
    except Exception as e:
        logger.error(f"Ошибка при получении назначенных заказов: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_all_orders(status=None):
    """Получение всех заказов из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if status:
            cursor.execute("""
                SELECT o.*, u.first_name, u.last_name
                FROM orders o
                LEFT JOIN users u ON o.dispatcher_id = u.user_id
                WHERE o.status = %s
                ORDER BY o.created_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT o.*, u.first_name, u.last_name
                FROM orders o
                LEFT JOIN users u ON o.dispatcher_id = u.user_id
                ORDER BY o.created_at DESC
            """)
        
        orders_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        orders = []
        for order_data in orders_data:
            # Создаем словарь с данными заказа
            order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
            
            # Получаем мастеров, назначенных на заказ
            cursor.execute("""
                SELECT a.*, u.first_name, u.last_name, u.username
                FROM assignments a
                JOIN users u ON a.technician_id = u.user_id
                WHERE a.order_id = %s
            """, (order_dict['order_id'],))
            
            technicians_data = cursor.fetchall()
            
            # Получаем имена столбцов для мастеров
            tech_column_names = [desc[0] for desc in cursor.description]
            
            technicians = []
            for tech_data in technicians_data:
                # Создаем словарь с данными мастера
                tech_dict = {tech_column_names[i]: tech_data[i] for i in range(len(tech_column_names))}
                technicians.append(tech_dict)
            
            order_dict['technicians'] = technicians
            order_dict['dispatcher_first_name'] = order_dict.get('first_name')
            order_dict['dispatcher_last_name'] = order_dict.get('last_name')
            
            orders.append(Order.from_dict(order_dict))
        
        return orders
    except Exception as e:
        logger.error(f"Ошибка при получении всех заказов: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def assign_order(order_id, technician_id, assigned_by):
    """Назначение заказа мастеру"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Добавляем новое назначение
        cursor.execute(
            "INSERT INTO assignments (order_id, technician_id, assigned_by) VALUES (%s, %s, %s) RETURNING assignment_id",
            (order_id, technician_id, assigned_by)
        )
        assignment_id = cursor.fetchone()[0]
        
        # Обновляем статус заказа, если он еще в статусе "новый"
        cursor.execute(
            "UPDATE orders SET status = 'assigned', updated_at = CURRENT_TIMESTAMP WHERE order_id = %s AND status = 'new'",
            (order_id,)
        )
        
        conn.commit()
        return assignment_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при назначении заказа мастеру: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_order_technicians(order_id):
    """Получение списка мастеров, назначенных на заказ"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.*, u.first_name, u.last_name, u.username
            FROM assignments a
            JOIN users u ON a.technician_id = u.user_id
            WHERE a.order_id = %s
        """, (order_id,))
        
        technicians_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        technicians = []
        for tech_data in technicians_data:
            # Создаем словарь с данными мастера
            tech_dict = {column_names[i]: tech_data[i] for i in range(len(column_names))}
            technicians.append(Assignment.from_dict(tech_dict))
        
        return technicians
    except Exception as e:
        logger.error(f"Ошибка при получении мастеров заказа: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def unassign_order(order_id, technician_id):
    """Отмена назначения заказа мастеру"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM assignments WHERE order_id = %s AND technician_id = %s",
            (order_id, technician_id)
        )
        rows_deleted = cursor.rowcount
        
        # Проверяем, остались ли еще техники на этот заказ
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE order_id = %s", (order_id,))
        remaining_techs = cursor.fetchone()[0]
        
        # Если не осталось мастеров и статус был 'assigned', возвращаем статус в 'new'
        if remaining_techs == 0:
            cursor.execute(
                "UPDATE orders SET status = 'new', updated_at = CURRENT_TIMESTAMP WHERE order_id = %s AND status = 'assigned'",
                (order_id,)
            )
        
        conn.commit()
        return rows_deleted > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при отмене назначения заказа: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def set_user_state(user_id, state, order_id=None):
    """Устанавливает состояние пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже запись о состоянии пользователя
        cursor.execute("SELECT user_id FROM user_states WHERE user_id = %s", (user_id,))
        existing_state = cursor.fetchone()
        
        if existing_state:
            # Обновляем существующее состояние
            cursor.execute(
                "UPDATE user_states SET state = %s, order_id = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                (state, order_id, user_id)
            )
        else:
            # Создаем новое состояние
            cursor.execute(
                "INSERT INTO user_states (user_id, state, order_id) VALUES (%s, %s, %s)",
                (user_id, state, order_id)
            )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при установке состояния пользователя: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_state(user_id):
    """Возвращает текущее состояние пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT state FROM user_states WHERE user_id = %s", (user_id,))
        state = cursor.fetchone()
        
        return state[0] if state else None
    except Exception as e:
        logger.error(f"Ошибка при получении состояния пользователя: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_current_order_id(user_id):
    """Возвращает ID текущего заказа пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT order_id FROM user_states WHERE user_id = %s", (user_id,))
        order_id = cursor.fetchone()
        
        return order_id[0] if order_id and order_id[0] is not None else None
    except Exception as e:
        logger.error(f"Ошибка при получении ID текущего заказа: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def clear_user_state(user_id):
    """Очищает состояние пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM user_states WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при очистке состояния пользователя: {e}")
        return False
    finally:
        cursor.close()
        conn.close()