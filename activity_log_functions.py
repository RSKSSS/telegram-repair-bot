@with_db_transaction
def add_activity_log(user_id, action_type, action_description, related_order_id=None, related_user_id=None, conn=None):
    """Добавление записи в лог активности
    
    Args:
        user_id: ID пользователя, совершившего действие
        action_type: Тип действия (например, 'order_create', 'status_update', 'user_delete')
        action_description: Описание действия
        related_order_id: ID заказа, связанного с действием (если есть)
        related_user_id: ID пользователя, связанного с действием (если есть)
        conn: Соединение с базой данных
    
    Returns:
        log_id: ID записи в логе или None в случае ошибки
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO activity_logs (user_id, action_type, action_description, related_order_id, related_user_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, action_type, action_description, related_order_id, related_user_id)
        )
        log_id = cursor.lastrowid
        log_id = cursor.fetchone()[0]
        return log_id
    except Exception as e:
        logger.error(f"Ошибка при добавлении записи в лог: {e}")
        return None
    finally:
        cursor.close()

@with_db_connection
def get_activity_logs(limit=50, offset=0, user_id=None, action_type=None, related_order_id=None, related_user_id=None, conn=None):
    """Получение логов активности с фильтрацией
    
    Args:
        limit: Максимальное количество записей для возврата
        offset: Смещение (для пагинации)
        user_id: Фильтр по ID пользователя, совершившего действие
        action_type: Фильтр по типу действия
        related_order_id: Фильтр по ID связанного заказа
        related_user_id: Фильтр по ID связанного пользователя
        conn: Соединение с базой данных
    
    Returns:
        logs: Список логов активности
    """
    cursor = conn.cursor()
    
    try:
        # Базовый запрос
        query = """
            SELECT al.*, 
                   u.first_name, u.last_name, u.username, u.role, 
                   o.client_name, o.client_phone, 
                   ru.first_name as related_first_name, ru.last_name as related_last_name, ru.username as related_username
            FROM activity_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            LEFT JOIN orders o ON al.related_order_id = o.order_id
            LEFT JOIN users ru ON al.related_user_id = ru.user_id
        """
        
        # Добавляем условия фильтрации
        conditions = []
        params = []
        
        if user_id is not None:
            conditions.append("al.user_id = %s")
            params.append(user_id)
        
        if action_type is not None:
            conditions.append("al.action_type = %s")
            params.append(action_type)
        
        if related_order_id is not None:
            conditions.append("al.related_order_id = %s")
            params.append(related_order_id)
        
        if related_user_id is not None:
            conditions.append("al.related_user_id = %s")
            params.append(related_user_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Добавляем сортировку и лимит
        query += " ORDER BY al.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Выполняем запрос
        cursor.execute(query, params)
        logs_data = cursor.fetchall()
        
        # Получаем имена столбцов
        column_names = [desc[0] for desc in cursor.description]
        
        # Формируем список результатов
        logs = []
        for log_data in logs_data:
            log_dict = {column_names[i]: log_data[i] for i in range(len(column_names))}
            logs.append(log_dict)
        
        return logs
    except Exception as e:
        logger.error(f"Ошибка при получении логов активности: {e}")
        return []
    finally:
        cursor.close()

@with_db_connection
def get_admin_activity_summary(days=7, conn=None):
    """Получение сводки активности для админа
    
    Args:
        days: Количество дней для анализа
        conn: Соединение с базой данных
    
    Returns:
        dict: Словарь со статистикой активности
    """
    cursor = conn.cursor()
    
    try:
        # Статистика по типам действий
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM activity_logs
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY action_type
            ORDER BY count DESC
        """, (days,))
        action_stats = cursor.fetchall()
        
        # Статистика по активности пользователей
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.last_name, u.username, u.role, COUNT(*) as activity_count
            FROM activity_logs al
            JOIN users u ON al.user_id = u.user_id
            WHERE al.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY u.user_id, u.first_name, u.last_name, u.username, u.role
            ORDER BY activity_count DESC
            LIMIT 10
        """, (days,))
        user_stats = cursor.fetchall()
        
        # Статистика по заказам
        cursor.execute("""
            SELECT o.order_id, o.client_name, COUNT(*) as activity_count
            FROM activity_logs al
            JOIN orders o ON al.related_order_id = o.order_id
            WHERE al.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY o.order_id, o.client_name
            ORDER BY activity_count DESC
            LIMIT 10
        """, (days,))
        order_stats = cursor.fetchall()
        
        # Формируем результат
        result = {
            'action_stats': [{'action_type': r[0], 'count': r[1]} for r in action_stats],
            'user_stats': [{'user_id': r[0], 'first_name': r[1], 'last_name': r[2], 'username': r[3], 'role': r[4], 'activity_count': r[5]} for r in user_stats],
            'order_stats': [{'order_id': r[0], 'client_name': r[1], 'activity_count': r[2]} for r in order_stats]
        }
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении сводки активности: {e}")
        return {'action_stats': [], 'user_stats': [], 'order_stats': []}
    finally:
        cursor.close()