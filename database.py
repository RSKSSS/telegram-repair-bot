import sqlite3
import json
import logging
from config import DATABASE_FILE

logger = logging.getLogger(__name__)

def dict_factory(cursor, row):
    """Convert database row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_connection():
    """Get a connection to the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = dict_factory
    return conn

def initialize_database():
    """Create the necessary tables if they don't exist"""
    logger.info("Initializing database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        role TEXT DEFAULT 'client',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        client_phone TEXT NOT NULL,
        client_name TEXT NOT NULL,
        client_address TEXT NOT NULL,
        problem_description TEXT NOT NULL,
        service_cost REAL,
        service_description TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_user(user_id, first_name, last_name=None, username=None, role='client'):
    """Save user information to the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, first_name, last_name, username, role)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, first_name, last_name, username, role))
    
    conn.commit()
    conn.close()
    return user_id

def get_user(user_id):
    """Get user information from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    return user

def get_user_role(user_id):
    """Get user role from the database"""
    user = get_user(user_id)
    if user:
        return user['role']
    return 'client'  # Default role

def get_all_users():
    """Get all users from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users ORDER BY role DESC, user_id ASC')
    users = cursor.fetchall()
    
    conn.close()
    return users

def update_user_role(user_id, role):
    """Update user role in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
    
    conn.commit()
    conn.close()
    return True

def save_order(user_id, client_phone, client_name, client_address, problem_description):
    """Save an order to the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO orders (user_id, client_phone, client_name, client_address, problem_description)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, client_phone, client_name, client_address, problem_description))
    
    order_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return order_id

def update_order(order_id, status=None, service_cost=None, service_description=None):
    """Update an order in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    update_fields = []
    params = []
    
    if status is not None:
        update_fields.append('status = ?')
        params.append(status)
    
    if service_cost is not None:
        update_fields.append('service_cost = ?')
        params.append(service_cost)
    
    if service_description is not None:
        update_fields.append('service_description = ?')
        params.append(service_description)
    
    if update_fields:
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        query = f"UPDATE orders SET {', '.join(update_fields)} WHERE order_id = ?"
        params.append(order_id)
        
        cursor.execute(query, params)
        
        conn.commit()
    
    conn.close()
    return True

def get_order(order_id):
    """Get an order from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    order = cursor.fetchone()
    
    conn.close()
    return order

def get_orders_by_user(user_id):
    """Get all orders by a specific user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM orders 
    WHERE user_id = ? 
    ORDER BY 
        CASE status
            WHEN 'new' THEN 1
            WHEN 'processing' THEN 2
            WHEN 'completed' THEN 3
            WHEN 'cancelled' THEN 4
            ELSE 5
        END,
        created_at DESC
    ''', (user_id,))
    
    orders = cursor.fetchall()
    
    conn.close()
    return orders

def get_orders_by_phone(phone):
    """Get all orders by a client phone number"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM orders 
    WHERE client_phone = ? 
    ORDER BY created_at DESC
    ''', (phone,))
    
    orders = cursor.fetchall()
    
    conn.close()
    return orders

def get_all_orders(status=None):
    """Get all orders from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute('''
        SELECT * FROM orders 
        WHERE status = ? 
        ORDER BY created_at DESC
        ''', (status,))
    else:
        cursor.execute('''
        SELECT * FROM orders 
        ORDER BY 
            CASE status
                WHEN 'new' THEN 1
                WHEN 'processing' THEN 2
                WHEN 'completed' THEN 3
                WHEN 'cancelled' THEN 4
                ELSE 5
            END,
            created_at DESC
        ''')
    
    orders = cursor.fetchall()
    
    conn.close()
    return orders
