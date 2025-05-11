import os
import datetime
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from typing import Optional, List, Dict, Any, Callable, Union
import functools
from logger import get_component_logger, log_function_call
from cache import cached, invalidate_cache_on_update, cache_clear

# Настройка логирования
logger = get_component_logger('database')

def is_postgres():
    """Проверяет, используется ли PostgreSQL"""
    # Проверяем специальную переменную окружения RENDER, которая есть только в Render
    # В Render она имеет значение 'true'
    if os.environ.get('RENDER') == 'true':
        return True
    # Также проверяем наличие DATABASE_URL как дополнительный признак PostgreSQL
    if os.environ.get('DATABASE_URL') and 'postgres' in os.environ.get('DATABASE_URL', ''):
        return True
    return False  # В локальной среде Replit используем SQLite

def get_placeholder():
    """Возвращает placeholder для SQL параметров в зависимости от типа БД"""
    global current_connection_is_postgres
    return '%s' if current_connection_is_postgres else '?'

# Переменная для отслеживания типа текущего подключения
# True - PostgreSQL, False - SQLite
current_connection_is_postgres = False

def get_connection():
    """Получение соединения с базой данных (PostgreSQL или SQLite)"""
    global current_connection_is_postgres
    
    try:
        # Проверяем, нужно ли использовать PostgreSQL
        if is_postgres():
            # В Render или если указана переменная DATABASE_URL используем PostgreSQL
            logger.info("Подключение к PostgreSQL в среде Render...")
            database_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(database_url)
            current_connection_is_postgres = True
            return conn
        else:
            # В локальной среде Replit используем SQLite
            logger.info("Подключение к SQLite в локальной среде...")
            conn = sqlite3.connect('service_bot.db')
            current_connection_is_postgres = False
            return conn
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        # В случае ошибки подключения к PostgreSQL, используем SQLite
        logger.warning("Использую запасной вариант - SQLite")
        conn = sqlite3.connect('service_bot.db')
        current_connection_is_postgres = False
        return conn
        
def check_database_connection() -> bool:
    """Проверка подключения к базе данных
    
    Returns:
        bool: True, если подключение успешно, иначе False
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, какой тип соединения используется - PostgreSQL или SQLite
        if os.environ.get('DATABASE_URL'):
            # PostgreSQL использует %s для параметров
            cursor.execute("SELECT 1")
        else:
            # SQLite использует ? для параметров
            cursor.execute("SELECT 1")
            
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Проверяем результат
        return result is not None and (result[0] == 1)
    except Exception as e:
        logger.error(f"Ошибка при проверке подключения к базе данных: {e}")
        return False

@log_function_call(logger)
def initialize_database():
    """Инициализация базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    use_postgres = is_postgres()

    # Разный синтаксис для PostgreSQL и SQLite
    if use_postgres:
        # PostgreSQL синтаксис
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            role TEXT DEFAULT 'user',
            is_approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            client_phone TEXT NOT NULL,
            client_name TEXT NOT NULL,
            problem_description TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dispatcher_id BIGINT,
            service_cost REAL,
            service_description TEXT,
            FOREIGN KEY (dispatcher_id) REFERENCES users(user_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id SERIAL PRIMARY KEY,
            order_id INTEGER,
            technician_id BIGINT,
            assigned_by BIGINT,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (technician_id) REFERENCES users(user_id),
            FOREIGN KEY (assigned_by) REFERENCES users(user_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            user_id BIGINT PRIMARY KEY,
            state TEXT NOT NULL,
            order_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS problem_templates (
            template_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_by BIGINT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            action_type TEXT NOT NULL,
            action_description TEXT NOT NULL,
            related_order_id INTEGER,
            related_user_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        # SQLite синтаксис
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            role TEXT DEFAULT 'user',
            is_approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_phone TEXT NOT NULL,
            client_name TEXT NOT NULL,
            problem_description TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dispatcher_id INTEGER,
            service_cost REAL,
            service_description TEXT,
            FOREIGN KEY (dispatcher_id) REFERENCES users(user_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            technician_id INTEGER,
            assigned_by INTEGER,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (technician_id) REFERENCES users(user_id),
            FOREIGN KEY (assigned_by) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_states (
        user_id INTEGER PRIMARY KEY,
        state TEXT NOT NULL,
        order_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Разные SQL-запросы в зависимости от типа базы данных
    if is_postgres:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS problem_templates (
            template_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_by BIGINT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS problem_templates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_by INTEGER,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    # Разные SQL-запросы в зависимости от типа базы данных
    if is_postgres:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            action_type TEXT NOT NULL,
            action_description TEXT NOT NULL,
            related_order_id INTEGER,
            related_user_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT NOT NULL,
            action_description TEXT NOT NULL,
            related_order_id INTEGER,
            related_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)


    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

def save_user(user_id: int, first_name: str, last_name: str = None, username: str = None) -> bool:
    """Сохранение информации о пользователе"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()

    try:
        # Проверяем, существует ли пользователь и сохраняем текущие значения
        cursor.execute(f"""
        SELECT role, is_approved FROM users WHERE user_id = {placeholder}
        """, (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Обновляем только личные данные, сохраняя роль и статус подтверждения
            cursor.execute(f"""
            UPDATE users SET username = {placeholder}, first_name = {placeholder}, last_name = {placeholder} 
            WHERE user_id = {placeholder}
            """, (username, first_name, last_name, user_id))
            logger.info(f"Обновлены данные существующего пользователя {user_id} с сохранением роли и статуса")
        else:
            # Создаем нового пользователя
            cursor.execute(f"""
            INSERT INTO users (user_id, username, first_name, last_name, role, is_approved)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 'user', FALSE)
            """, (user_id, username, first_name, last_name))
            logger.info(f"Создан новый пользователь {user_id}")
            
            # Если это первый пользователь, делаем его администратором
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 1:
                cursor.execute(f"""
                UPDATE users SET role = 'admin', is_approved = TRUE
                WHERE user_id = {placeholder}
                """, (user_id,))
                logger.info(f"Первый пользователь {user_id} назначен администратором")

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя: {e}")
        return False
    finally:
        conn.close()

@cached('users')
def get_user(user_id: int) -> Optional[Dict]:
    """
    Получение информации о пользователе с использованием кэширования.
    Кэш обновляется автоматически при изменении данных пользователя.
    
    Args:
        user_id: ID пользователя в Telegram
        
    Returns:
        Dict: Словарь с информацией о пользователе или None, если пользователь не найден
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()

    try:
        cursor.execute(f"""
        SELECT user_id, username, first_name, last_name, role, is_approved
        FROM users WHERE user_id = {placeholder}
        """, (user_id,))

        user = cursor.fetchone()
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'role': user[4],
                'is_approved': bool(user[5])
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
        return None
    finally:
        conn.close()

def get_user_role(user_id: int) -> Optional[str]:
    """Получение роли пользователя"""
    user = get_user(user_id)
    return user['role'] if user else None

def get_all_users():
    """Получение всех пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        user_list = []
        for user_data in users:
            user_dict = {column_names[i]: user_data[i] for i in range(len(column_names))}
            user_list.append(user_dict)
        return user_list
    except Exception as e:
        logger.error(f"Ошибка при получении всех пользователей: {e}")
        return []
    finally:
        conn.close()

@cached('technicians')
def get_technicians():
    """
    Получение всех техников с использованием кэширования.
    
    Returns:
        List[Dict]: Список словарей с информацией о техниках
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE role = 'technician' AND is_approved = TRUE")
        technicians = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        technician_list = []
        for technician_data in technicians:
            technician_dict = {column_names[i]: technician_data[i] for i in range(len(column_names))}
            technician_list.append(technician_dict)
        return technician_list
    except Exception as e:
        logger.error(f"Ошибка при получении всех техников: {e}")
        return []
    finally:
        conn.close()

@invalidate_cache_on_update('users')
def update_user_role(user_id: int, role: str) -> bool:
    """
    Обновление роли пользователя с автоматической инвалидацией кэша.
    
    Args:
        user_id: ID пользователя
        role: Новая роль пользователя
        
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"UPDATE users SET role = {placeholder} WHERE user_id = {placeholder}", (role, user_id))
        conn.commit()
        logger.info(f"Роль пользователя {user_id} успешно обновлена на {role}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении роли пользователя {user_id}: {e}")
        return False
    finally:
        conn.close()

def approve_user(user_id: int) -> bool:
    """Подтверждение пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        if is_postgres():
            cursor.execute(f"UPDATE users SET is_approved = TRUE WHERE user_id = {placeholder}", (user_id,))
        else:
            cursor.execute(f"UPDATE users SET is_approved = 1 WHERE user_id = {placeholder}", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при подтверждении пользователя: {e}")
        return False
    finally:
        conn.close()

def reject_user(user_id: int) -> bool:
    """Отклонение пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"DELETE FROM users WHERE user_id = {placeholder}", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при отклонении пользователя: {e}")
        return False
    finally:
        conn.close()

def is_user_approved(user_id: int) -> bool:
    """Проверка, подтвержден ли пользователь"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT is_approved FROM users WHERE user_id = {placeholder}", (user_id,))
        approved = cursor.fetchone()
        
        # В PostgreSQL и SQLite логические значения представлены по-разному
        if approved:
            if is_postgres():
                # В PostgreSQL логические значения уже преобразованы в bool
                result = approved[0]
            else:
                # В SQLite логические значения хранятся как 0 и 1
                result = bool(approved[0])
        else:
            result = False
            
        logger.info(f"Проверка подтверждения пользователя {user_id}: {result}, raw_data: {approved}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке, подтвержден ли пользователь {user_id}: {e}")
        return False
    finally:
        conn.close()

def get_unapproved_users():
    """Получение всех неподтвержденных пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # В PostgreSQL логические значения используются по-другому
        if is_postgres():
            cursor.execute("SELECT * FROM users WHERE is_approved = FALSE")
        else:
            cursor.execute("SELECT * FROM users WHERE is_approved = 0")
            
        users = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        user_list = []
        for user_data in users:
            user_dict = {column_names[i]: user_data[i] for i in range(len(column_names))}
            user_list.append(user_dict)
        return user_list
    except Exception as e:
        logger.error(f"Ошибка при получении неподтвержденных пользователей: {e}")
        return []
    finally:
        conn.close()

def save_order(dispatcher_id: int, client_phone: str, client_name: str, problem_description: str, client_address: str, scheduled_datetime: str = None) -> Optional[int]:
    """
    Сохранение заказа с инвалидацией кэша всех заказов
    
    Args:
        dispatcher_id: ID диспетчера, создавшего заказ
        client_phone: Телефон клиента
        client_name: Имя клиента
        problem_description: Описание проблемы
        client_address: Адрес клиента
        scheduled_datetime: Запланированное время выполнения
        
    Returns:
        Optional[int]: ID созданного заказа или None в случае ошибки
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Определяем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        # Если используется PostgreSQL, то для получения ID созданной записи нужно использовать RETURNING
        if is_postgres():
            cursor.execute(f"""
            INSERT INTO orders (dispatcher_id, client_phone, client_name, problem_description, client_address, scheduled_datetime)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            RETURNING order_id
            """, (dispatcher_id, client_phone, client_name, problem_description, client_address, scheduled_datetime))
            # В PostgreSQL order_id возвращается из запроса RETURNING
            result = cursor.fetchone()
            order_id = result[0] if result else None
        else:
            # SQLite
            cursor.execute(f"""
            INSERT INTO orders (dispatcher_id, client_phone, client_name, problem_description, client_address, scheduled_datetime)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (dispatcher_id, client_phone, client_name, problem_description, client_address, scheduled_datetime))
            order_id = cursor.lastrowid
            
        conn.commit()
        
        # Инвалидируем кэш всех заказов
        cache_clear('orders')
        return order_id
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказа: {e}")
        return None
    finally:
        conn.close()

@invalidate_cache_on_update('orders')
def update_order_status(order_id: int, new_status: int) -> bool:
    """
    Обновляет статус заказа
    
    Args:
        order_id: ID заказа
        new_status: Новый статус заказа
        
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    try:
        conn = get_connection()
        conn.execute("""
            UPDATE orders 
            SET status = ? 
            WHERE order_id = ?
        """, (new_status, order_id))
        conn.commit()
        
        # Инвалидируем кэш всех заказов
        cache_clear('orders')
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса заказа: {e}")
        return False
    finally:
        conn.close()

@invalidate_cache_on_update('orders')
def update_order(order_id: int, data=None, status: str = None, service_cost: float = None, service_description: str = None, scheduled_datetime: str = None) -> bool:
    """
    Обновление заказа с автоматической инвалидацией кэша.
    
    Args:
        order_id: ID заказа
        data: Словарь с параметрами для обновления (ключи: status, technician_id, service_cost, service_description, scheduled_datetime)
        status: Новый статус заказа (устаревший параметр, используйте data)
        service_cost: Новая стоимость услуг (устаревший параметр, используйте data)
        service_description: Новое описание услуг (устаревший параметр, используйте data)
        scheduled_datetime: Новое время исполнения заказа (устаревший параметр, используйте data)
        
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        update_fields = []
        update_values = []

        # Используем переданный словарь data, если он есть
        if data and isinstance(data, dict):
            if 'status' in data and data['status']:
                update_fields.append(f"status = {placeholder}")
                update_values.append(data['status'])
            if 'technician_id' in data:
                update_fields.append(f"technician_id = {placeholder}")
                update_values.append(data['technician_id'])
            if 'service_cost' in data and data['service_cost']:
                update_fields.append(f"service_cost = {placeholder}")
                update_values.append(data['service_cost'])
            if 'service_description' in data and data['service_description']:
                update_fields.append(f"service_description = {placeholder}")
                update_values.append(data['service_description'])
            if 'scheduled_datetime' in data and data['scheduled_datetime']:
                update_fields.append(f"scheduled_datetime = {placeholder}")
                update_values.append(data['scheduled_datetime'])
        else:
            # Поддержка обратной совместимости
            if status:
                update_fields.append(f"status = {placeholder}")
                update_values.append(status)
            if service_cost:
                update_fields.append(f"service_cost = {placeholder}")
                update_values.append(service_cost)
            if service_description:
                update_fields.append(f"service_description = {placeholder}")
                update_values.append(service_description)
            if scheduled_datetime:
                update_fields.append(f"scheduled_datetime = {placeholder}")
                update_values.append(scheduled_datetime)

        if update_fields:
            sql = f"UPDATE orders SET {', '.join(update_fields)} WHERE order_id = {placeholder}"
            update_values.append(order_id)
            cursor.execute(sql, tuple(update_values))
            conn.commit()
            
            # Логируем информацию об обновлении для отладки
            logger.info(f"Заказ {order_id} успешно обновлен: {', '.join(update_fields)}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении заказа {order_id}: {e}")
        return False
    finally:
        conn.close()

@cached('orders')
def get_order(order_id: int) -> Optional[Dict]:
    """
    Получение заказа с использованием кэширования.
    Кэш обновляется автоматически при изменении заказа.
    
    Args:
        order_id: ID заказа
        
    Returns:
        Dict: Словарь с информацией о заказе или None, если заказ не найден
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT * FROM orders WHERE order_id = {placeholder}", (order_id,))
        order = cursor.fetchone()
        if order:
            column_names = [desc[0] for desc in cursor.description]
            order_dict = {column_names[i]: order[i] for i in range(len(column_names))}
            return order_dict
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении заказа: {e}")
        return None
    finally:
        conn.close()

def get_orders_by_user(user_id: int) -> List[Dict]:
    """Получение заказов пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT * FROM orders WHERE dispatcher_id = {placeholder}", (user_id,))
        orders = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        order_list = []
        for order_data in orders:
            order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
            order_list.append(order_dict)
        return order_list
    except Exception as e:
        logger.error(f"Ошибка при получении заказов пользователя: {e}")
        return []
    finally:
        conn.close()

def get_assigned_orders(technician_id: int) -> List[Dict]:
    """Получение назначенных заказов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"""
            SELECT o.* FROM orders o
            JOIN order_technicians a ON o.order_id = a.order_id
            WHERE a.technician_id = {placeholder}
        """, (technician_id,))
        orders = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        order_list = []
        for order_data in orders:
            order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
            order_list.append(order_dict)
        return order_list
    except Exception as e:
        logger.error(f"Ошибка при получении назначенных заказов: {e}")
        return []
    finally:
        conn.close()

@cached('orders', lambda status=None: f'all_orders_{status or "all"}')
def get_all_orders(status: str = None) -> List[Dict]:
    """
    Получение всех заказов с использованием кэширования.
    
    Args:
        status: Опциональный фильтр по статусу заказа
        
    Returns:
        List[Dict]: Список словарей с информацией о заказах
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        if status:
            cursor.execute(f"SELECT * FROM orders WHERE status = {placeholder}", (status,))
        else:
            cursor.execute("SELECT * FROM orders")
        orders = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        order_list = []
        for order_data in orders:
            order_dict = {column_names[i]: order_data[i] for i in range(len(column_names))}
            order_list.append(order_dict)
        return order_list
    except Exception as e:
        logger.error(f"Ошибка при получении всех заказов: {e}")
        return []
    finally:
        conn.close()

def assign_order(order_id: int, technician_id: int, assigned_by: int) -> Optional[int]:
    """Назначение заказа"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        # Для назначения используем правильное имя таблицы order_technicians
        cursor.execute(f"""
            INSERT INTO order_technicians (order_id, technician_id, assigned_by)
            VALUES ({placeholder}, {placeholder}, {placeholder})
        """, (order_id, technician_id, assigned_by))
        conn.commit()
        
        # Для PostgreSQL и SQLite получение ID последней вставленной записи отличается
        if is_postgres():
            cursor.execute("SELECT lastval()")
            return cursor.fetchone()[0]
        else:
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Ошибка при назначении заказа: {e}")
        return None
    finally:
        conn.close()

def get_order_technicians(order_id: int) -> List[Dict]:
    """Получение техников заказа"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"""
            SELECT u.* FROM users u
            JOIN order_technicians a ON u.user_id = a.technician_id
            WHERE a.order_id = {placeholder}
        """, (order_id,))
        technicians = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        technician_list = []
        for technician_data in technicians:
            technician_dict = {column_names[i]: technician_data[i] for i in range(len(column_names))}
            technician_list.append(technician_dict)
        return technician_list
    except Exception as e:
        logger.error(f"Ошибка при получении техников заказа: {e}")
        return []
    finally:
        conn.close()

def unassign_order(order_id: int, technician_id: int) -> bool:
    """Отмена назначения заказа"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"""
            DELETE FROM order_technicians WHERE order_id = {placeholder} AND technician_id = {placeholder}
        """, (order_id, technician_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при отмене назначения заказа: {e}")
        return False
    finally:
        conn.close()

def set_user_state(user_id: int, state: str, order_id: Optional[int] = None) -> bool:
    """Установка состояния пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        # Для PostgreSQL используем другой синтаксис вместо INSERT OR REPLACE
        if is_postgres():
            # Сначала пробуем удалить существующую запись
            cursor.execute(f"DELETE FROM user_states WHERE user_id = {placeholder}", (user_id,))
            # Затем делаем вставку
            cursor.execute(f"""
                INSERT INTO user_states (user_id, state, order_id)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            """, (user_id, state, order_id))
        else:
            # Для SQLite используем INSERT OR REPLACE
            cursor.execute(f"""
                INSERT OR REPLACE INTO user_states (user_id, state, order_id)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            """, (user_id, state, order_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке состояния пользователя: {e}")
        return False
    finally:
        conn.close()

def get_user_state(user_id: int) -> Optional[str]:
    """Получение состояния пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT state FROM user_states WHERE user_id = {placeholder}", (user_id,))
        state = cursor.fetchone()
        return state[0] if state else None
    except Exception as e:
        logger.error(f"Ошибка при получении состояния пользователя: {e}")
        return None
    finally:
        conn.close()

def get_current_order_id(user_id: int) -> Optional[int]:
    """Получение ID текущего заказа"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT order_id FROM user_states WHERE user_id = {placeholder}", (user_id,))
        order_id = cursor.fetchone()
        return order_id[0] if order_id else None
    except Exception as e:
        logger.error(f"Ошибка при получении ID текущего заказа: {e}")
        return None
    finally:
        conn.close()

def clear_user_state(user_id: int) -> bool:
    """Очистка состояния пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"DELETE FROM user_states WHERE user_id = {placeholder}", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке состояния пользователя: {e}")
        return False
    finally:
        conn.close()

def save_problem_template(title: str, description: str, created_by: int) -> Optional[int]:
    """Сохранение шаблона проблемы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"""
            INSERT INTO problem_templates (title, description, created_by)
            VALUES ({placeholder}, {placeholder}, {placeholder})
        """, (title, description, created_by))
        conn.commit()
        
        # Для PostgreSQL и SQLite получение ID последней вставленной записи отличается
        if is_postgres():
            cursor.execute("SELECT lastval()")
            return cursor.fetchone()[0]
        else:
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Ошибка при сохранении шаблона проблемы: {e}")
        return None
    finally:
        conn.close()

def update_problem_template(template_id: int, title: str = None, description: str = None, is_active: bool = None) -> bool:
    """Обновление шаблона проблемы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        update_fields = []
        update_values = []

        if title:
            update_fields.append(f"title = {placeholder}")
            update_values.append(title)
        if description:
            update_fields.append(f"description = {placeholder}")
            update_values.append(description)
        if is_active is not None:
            update_fields.append(f"is_active = {placeholder}")
            update_values.append(is_active)

        if update_fields:
            sql = f"UPDATE problem_templates SET {', '.join(update_fields)} WHERE template_id = {placeholder}"
            update_values.append(template_id)
            cursor.execute(sql, tuple(update_values))
            conn.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении шаблона проблемы: {e}")
        return False
    finally:
        conn.close()

def get_problem_template(template_id: int) -> Optional[Dict]:
    """Получение шаблона проблемы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT * FROM problem_templates WHERE template_id = {placeholder}", (template_id,))
        template = cursor.fetchone()
        if template:
            column_names = [desc[0] for desc in cursor.description]
            template_dict = {column_names[i]: template[i] for i in range(len(column_names))}
            return template_dict
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении шаблона проблемы: {e}")
        return None
    finally:
        conn.close()

def get_problem_templates(created_by: int = None, active_only: bool = True) -> List[Dict]:
    """Получение шаблонов проблем"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        conditions = []
        params = []

        if created_by:
            conditions.append(f"created_by = {placeholder}")
            params.append(created_by)
        if active_only:
            conditions.append("is_active = TRUE")

        sql = "SELECT * FROM problem_templates"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        cursor.execute(sql, tuple(params))
        templates = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        template_list = []
        for template_data in templates:
            template_dict = {column_names[i]: template_data[i] for i in range(len(column_names))}
            template_list.append(template_dict)
        return template_list
    except Exception as e:
        logger.error(f"Ошибка при получении шаблонов проблем: {e}")
        return []
    finally:
        conn.close()

def delete_problem_template(template_id: int) -> bool:
    """Удаление шаблона проблемы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"DELETE FROM problem_templates WHERE template_id = {placeholder}", (template_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении шаблона проблемы: {e}")
        return False
    finally:
        conn.close()

def delete_user(user_id: int) -> bool:
    """Удаление пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"DELETE FROM users WHERE user_id = {placeholder}", (user_id,))
        conn.commit()
        # Очищаем кэш пользователей
        cache_clear('users')
        logger.info(f"Пользователь {user_id} успешно удален, кэш очищен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя: {e}")
        return False
    finally:
        conn.close()

def delete_order(order_id: int) -> bool:
    """
    Удаление заказа с инвалидацией кэша
    
    Args:
        order_id: ID заказа для удаления
        
    Returns:
        bool: True, если заказ успешно удален, иначе False
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"DELETE FROM orders WHERE order_id = {placeholder}", (order_id,))
        conn.commit()
        
        # Инвалидируем кэш заказа и списков заказов
        # используем cache_clear, так как cache_delete может быть не определена
        cache_clear('orders')  # Очищаем весь кэш заказов
        
        logger.info(f"Заказ {order_id} успешно удален, кэш очищен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении заказа {order_id}: {e}")
        return False
    finally:
        conn.close()

def add_activity_log(user_id: int, action_type: str, action_description: str, related_order_id: int = None, related_user_id: int = None) -> Optional[int]:
    """Добавление лога активности"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"""
            INSERT INTO activity_logs (user_id, action_type, action_description, related_order_id, related_user_id)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (user_id, action_type, action_description, related_order_id, related_user_id))
        conn.commit()
        
        # Для PostgreSQL и SQLite получение ID последней вставленной записи отличается
        if is_postgres():
            cursor.execute("SELECT lastval()")
            return cursor.fetchone()[0]
        else:
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Ошибка при добавлении лога активности: {e}")
        return None
    finally:
        conn.close()

def get_activity_logs(limit: int = 50, offset: int = 0, user_id: int = None, action_type: str = None, related_order_id: int = None, related_user_id: int = None) -> List[Dict]:
    """Получение логов активности"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем placeholder в зависимости от типа БД
    placeholder = get_placeholder()
    
    try:
        conditions = []
        params = []

        if user_id:
            conditions.append(f"user_id = {placeholder}")
            params.append(user_id)
        if action_type:
            conditions.append(f"action_type = {placeholder}")
            params.append(action_type)
        if related_order_id:
            conditions.append(f"related_order_id = {placeholder}")
            params.append(related_order_id)
        if related_user_id:
            conditions.append(f"related_user_id = {placeholder}")
            params.append(related_user_id)

        sql = "SELECT * FROM activity_logs"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += f" LIMIT {placeholder} OFFSET {placeholder}"
        params.extend([limit, offset])

        cursor.execute(sql, tuple(params))
        logs = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        log_list = []
        for log_data in logs:
            log_dict = {column_names[i]: log_data[i] for i in range(len(column_names))}
            log_list.append(log_dict)
        return log_list
    except Exception as e:
        logger.error(f"Ошибка при получении логов активности: {e}")
        return []
    finally:
        conn.close()

def get_admin_activity_summary(days: int = 7) -> Dict:
    """Получение сводки активности админа"""
    # This function requires multiple queries and aggregation, which is better suited for more advanced databases.
    # For simplicity, we will return empty lists.
    return {'action_stats': [], 'user_stats': [], 'order_stats': []}