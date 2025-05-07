import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Получение соединения с PostgreSQL базой данных"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

def initialize_database():
    """Инициализация базы данных - создание таблиц если они не существуют"""
    logger.info("Инициализация базы данных...")
    conn = get_connection()
    if not conn:
        logger.error("Не удалось подключиться к базе данных")
        return False
    
    try:
        with conn.cursor() as cursor:
            # Таблица пользователей
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                username TEXT,
                role TEXT NOT NULL DEFAULT 'technician',
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Таблица заказов
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                dispatcher_id BIGINT REFERENCES users(user_id),
                client_phone TEXT NOT NULL,
                client_name TEXT NOT NULL,
                client_address TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                service_cost NUMERIC,
                service_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Таблица назначений заказов техникам
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                technician_id BIGINT REFERENCES users(user_id),
                assigned_by BIGINT REFERENCES users(user_id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info("База данных инициализирована успешно")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Функции для работы с пользователями
def save_user(user_id, first_name, last_name=None, username=None, role='technician', is_approved=False):
    """Сохранение информации о пользователе в базу данных"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Проверяем, существует ли пользователь
            cursor.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
            if cursor.fetchone():
                # Обновляем существующего пользователя
                cursor.execute('''
                UPDATE users 
                SET first_name = %s, last_name = %s, username = %s 
                WHERE user_id = %s
                ''', (first_name, last_name, username, user_id))
            else:
                # Проверяем, есть ли уже пользователи в системе
                cursor.execute('SELECT COUNT(*) FROM users')
                result = cursor.fetchone()
                count = result[0] if result else 0
                
                # Если пользователей еще нет, то первый пользователь - администратор и утвержден по умолчанию
                if count == 0:
                    role = 'admin'
                    is_approved = True
                
                # Добавляем нового пользователя
                cursor.execute('''
                INSERT INTO users (user_id, first_name, last_name, username, role, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, first_name, last_name, username, role, is_approved))
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user(user_id):
    """Получение информации о пользователе из базы данных"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        return None
    finally:
        conn.close()

def get_user_role(user_id):
    """Получение роли пользователя из базы данных"""
    user = get_user(user_id)
    return user['role'] if user else None

def get_all_users():
    """Получение всех пользователей из базы данных"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении всех пользователей: {e}")
        return []
    finally:
        conn.close()

def get_technicians():
    """Получение всех техников из базы данных"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE role = 'technician' ORDER BY first_name")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении техников: {e}")
        return []
    finally:
        conn.close()

def update_user_role(user_id, role):
    """Обновление роли пользователя в базе данных"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE users SET role = %s WHERE user_id = %s', (role, user_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении роли пользователя: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def approve_user(user_id):
    """Подтверждение пользователя администратором"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE users SET is_approved = TRUE WHERE user_id = %s', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при подтверждении пользователя: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def reject_user(user_id):
    """Отклонение пользователя администратором"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при отклонении пользователя: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def is_user_approved(user_id):
    """Проверка, подтвержден ли пользователь администратором"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT is_approved FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса подтверждения пользователя: {e}")
        return False
    finally:
        conn.close()

def get_unapproved_users():
    """Получение всех неподтвержденных пользователей"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('SELECT * FROM users WHERE is_approved = FALSE ORDER BY created_at')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении неподтвержденных пользователей: {e}")
        return []
    finally:
        conn.close()

# Функции для работы с заказами
def save_order(dispatcher_id, client_phone, client_name, client_address, problem_description):
    """Сохранение заказа в базу данных"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
            INSERT INTO orders 
            (dispatcher_id, client_phone, client_name, client_address, problem_description) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING order_id
            ''', (dispatcher_id, client_phone, client_name, client_address, problem_description))
            
            result = cursor.fetchone()
            if result:
                order_id = result[0]
                conn.commit()
                return order_id
            conn.rollback()
            return None
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказа: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def update_order(order_id, status=None, service_cost=None, service_description=None):
    """Обновление заказа в базе данных"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            updates = []
            params = []
            
            if status is not None:
                updates.append("status = %s")
                params.append(status)
            
            if service_cost is not None:
                updates.append("service_cost = %s")
                params.append(service_cost)
            
            if service_description is not None:
                updates.append("service_description = %s")
                params.append(service_description)
            
            if not updates:
                return False
            
            updates.append("updated_at = %s")
            params.append(datetime.now())
            params.append(order_id)
            
            query = f"UPDATE orders SET {', '.join(updates)} WHERE order_id = %s"
            cursor.execute(query, params)
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении заказа: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_order(order_id):
    """Получение заказа из базы данных"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('''
            SELECT o.*, 
                   u.first_name as dispatcher_first_name, 
                   u.last_name as dispatcher_last_name 
            FROM orders o 
            LEFT JOIN users u ON o.dispatcher_id = u.user_id 
            WHERE o.order_id = %s
            ''', (order_id,))
            
            order = cursor.fetchone()
            
            if order:
                # Получаем информацию о назначенных техниках
                cursor.execute('''
                SELECT a.*, u.first_name, u.last_name, u.username 
                FROM assignments a 
                JOIN users u ON a.technician_id = u.user_id 
                WHERE a.order_id = %s
                ''', (order_id,))
                
                technicians = cursor.fetchall()
                order['technicians'] = technicians
            
            return order
    except Exception as e:
        logger.error(f"Ошибка при получении заказа: {e}")
        return None
    finally:
        conn.close()

def get_orders_by_user(user_id):
    """Получение всех заказов созданных пользователем (для диспетчера)"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('''
            SELECT * FROM orders WHERE dispatcher_id = %s 
            ORDER BY created_at DESC
            ''', (user_id,))
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении заказов пользователя: {e}")
        return []
    finally:
        conn.close()

def get_assigned_orders(technician_id):
    """Получение заказов, назначенных технику"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('''
            SELECT o.* FROM orders o 
            JOIN assignments a ON o.order_id = a.order_id 
            WHERE a.technician_id = %s 
            ORDER BY o.created_at DESC
            ''', (technician_id,))
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении назначенных заказов: {e}")
        return []
    finally:
        conn.close()

def get_all_orders(status=None):
    """Получение всех заказов из базы данных"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if status:
                cursor.execute('''
                SELECT * FROM orders WHERE status = %s 
                ORDER BY created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                SELECT * FROM orders ORDER BY created_at DESC
                ''')
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении всех заказов: {e}")
        return []
    finally:
        conn.close()

# Функции для работы с назначениями
def assign_order(order_id, technician_id, assigned_by):
    """Назначение заказа технику"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Проверяем, не назначен ли уже заказ этому технику
            cursor.execute('''
            SELECT assignment_id FROM assignments 
            WHERE order_id = %s AND technician_id = %s
            ''', (order_id, technician_id))
            
            if cursor.fetchone():
                # Уже назначен
                return True
            
            # Назначаем заказ технику
            cursor.execute('''
            INSERT INTO assignments (order_id, technician_id, assigned_by) 
            VALUES (%s, %s, %s)
            ''', (order_id, technician_id, assigned_by))
            
            # Обновляем статус заказа, если он новый
            cursor.execute('''
            UPDATE orders SET status = 'assigned' 
            WHERE order_id = %s AND status = 'new'
            ''', (order_id,))
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при назначении заказа: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_order_technicians(order_id):
    """Получение списка техников, назначенных на заказ"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute('''
            SELECT u.* FROM users u
            JOIN assignments a ON u.user_id = a.technician_id
            WHERE a.order_id = %s
            ''', (order_id,))
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка при получении техников для заказа: {e}")
        return []
    finally:
        conn.close()

def unassign_order(order_id, technician_id):
    """Отмена назначения заказа технику"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
            DELETE FROM assignments 
            WHERE order_id = %s AND technician_id = %s
            ''', (order_id, technician_id))
            
            # Проверяем, остались ли другие техники на этом заказе
            cursor.execute('''
            SELECT COUNT(*) FROM assignments WHERE order_id = %s
            ''', (order_id,))
            
            result = cursor.fetchone()
            if result is not None:
                count = result[0]
            else:
                count = 0
            
            # Если нет других техников, меняем статус на "новый"
            if count == 0:
                cursor.execute('''
                UPDATE orders SET status = 'new' 
                WHERE order_id = %s AND status = 'assigned'
                ''', (order_id,))
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при отмене назначения заказа: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()