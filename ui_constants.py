"""
Константы для улучшения пользовательского интерфейса бота
"""

# Эмодзи для различных действий и статусов
EMOJI = {
    # Статусы заказов
    'new': '🆕',
    'assigned': '👨‍🔧',
    'in_progress': '🔧',
    'completed': '✅',
    'cancelled': '❌',
    
    # Роли пользователей
    'admin': '👑',
    'dispatcher': '📋',
    'technician': '🔧',
    
    # Дополнительные иконки для разделов
    'main_menu': '🏠',
    'orders': '📝',
    'users': '👥',
    'settings': '⚙️',
    'back': '🔙',
    'help': '❓',
    'logs': '📊',
    'notification': '🔔',
    'phone': '📱',
    'address': '🏠',
    'date': '📅',
    'time': '🕒',
    'cost': '💰',
    'description': '📄',
    'filter': '🔍',
    'add': '➕',
    'delete': '🗑️',
    'edit': '✏️',
    'approve': '✅',
    'reject': '❌',
    'warning': '⚠️',
    'error': '❗',
    'success': '✅',
    'info': 'ℹ️',
}

# Форматирование для сообщений
HEADER_STYLE = "===== {} =====\n"
DIVIDER = "\n—————————————————\n"
BULLET = "• "
NUMBERED = "{}. "
BOLD = "*{}*"
ITALIC = "_{}_"
CODE = "`{}`"

# Метки для действий
ACTION_LABELS = {
    'order_create': 'Создание заказа',
    'order_update': 'Обновление заказа',
    'order_delete': 'Удаление заказа',
    'status_update': 'Изменение статуса',
    'technician_assign': 'Назначение мастера',
    'cost_update': 'Обновление стоимости',
    'description_update': 'Обновление описания работ',
    'user_add': 'Добавление пользователя',
    'user_delete': 'Удаление пользователя',
    'user_approve': 'Подтверждение пользователя',
    'user_reject': 'Отклонение пользователя',
    'role_update': 'Изменение роли',
}

# Улучшенные описания статусов
STATUS_DESCRIPTIONS = {
    'new': 'Новый заказ, ожидает назначения мастера',
    'assigned': 'Заказ назначен мастеру, ожидает начала работ',
    'in_progress': 'Мастер приступил к выполнению заказа',
    'completed': 'Заказ успешно выполнен',
    'cancelled': 'Заказ отменен'
}

def format_order_card(order, include_cost=True, include_description=True):
    """
    Форматирует карточку заказа для более удобного отображения
    
    Args:
        order: Словарь с данными заказа
        include_cost: Включать ли информацию о стоимости
        include_description: Включать ли описание работ
        
    Returns:
        Отформатированная строка с информацией о заказе
    """
    status = order.get('status', 'new')
    status_emoji = EMOJI.get(status, '')
    
    # Формируем заголовок с ID и статусом
    order_id = order.get('order_id', '')
    status = order.get('status', 'new')
    status_descr = STATUS_DESCRIPTIONS.get(status, 'Статус неизвестен')
    result = f"{BOLD.format('Заказ #' + str(order_id))} {status_emoji} {ITALIC.format(status_descr)}\n\n"
    
    # Информация о клиенте
    client_name = order.get('client_name', 'Н/Д')
    client_phone = order.get('client_phone', 'Н/Д')
    client_address = order.get('client_address', 'Н/Д')
    result += f"{EMOJI['phone']} *Клиент:* {client_name}\n"
    result += f"{EMOJI['phone']} *Телефон:* {client_phone}\n"
    result += f"{EMOJI['address']} *Адрес:* {client_address}\n"
    
    # Дата и время
    if order.get('scheduled_datetime'):
        scheduled_time = order.get('scheduled_datetime').strftime('%d.%m.%Y %H:%M')
        result += f"{EMOJI['date']} *Дата визита:* {scheduled_time}\n"
    
    # Проблема
    problem_descr = order.get('problem_description', 'Не указано')
    result += f"\n{EMOJI['description']} *Описание проблемы:*\n{problem_descr}\n"
    
    # Стоимость (если запрошена и есть)
    if include_cost and order.get('service_cost'):
        service_cost = order.get('service_cost')
        result += f"\n{EMOJI['cost']} *Стоимость услуг:* {service_cost} руб.\n"
    
    # Описание выполненных работ (если запрошено и есть)
    if include_description and order.get('service_description'):
        service_descr = order.get('service_description')
        result += f"\n{EMOJI['description']} *Выполненные работы:*\n{service_descr}\n"
    
    return result


def get_welcome_message(user_name):
    """
    Возвращает приветственное сообщение для пользователя
    
    Args:
        user_name: Имя пользователя
        
    Returns:
        Строка с приветственным сообщением
    """
    return f"""
{EMOJI['info']} Добро пожаловать, {BOLD.format(user_name)}!

Этот бот поможет вам управлять заказами на ремонт компьютерной техники.

{EMOJI['help']} Используйте кнопки меню для навигации или отправьте /help для получения справки.
"""

def format_error_message(message):
    """
    Форматирует сообщение об ошибке
    
    Args:
        message: Текст сообщения об ошибке
        
    Returns:
        Отформатированная строка с сообщением об ошибке
    """
    return f"{EMOJI['error']} {BOLD.format('Ошибка')}: {message}"

def format_success_message(message):
    """
    Форматирует сообщение об успешном выполнении операции
    
    Args:
        message: Текст сообщения
        
    Returns:
        Отформатированная строка с сообщением об успехе
    """
    return f"{EMOJI['success']} {BOLD.format('Успешно')}: {message}"

def format_warning_message(message):
    """
    Форматирует предупреждение
    
    Args:
        message: Текст предупреждения
        
    Returns:
        Отформатированная строка с предупреждением
    """
    return f"{EMOJI['warning']} {BOLD.format('Внимание')}: {message}"

def format_info_message(message):
    """
    Форматирует информационное сообщение
    
    Args:
        message: Текст сообщения
        
    Returns:
        Отформатированная строка с информационным сообщением
    """
    return f"{EMOJI['info']} {message}"

def format_help_section(title, items):
    """
    Форматирует раздел справки
    
    Args:
        title: Заголовок раздела
        items: Список словарей с ключами 'command' и 'description'
        
    Returns:
        Отформатированная строка с разделом справки
    """
    result = f"{BOLD.format(title)}:\n"
    
    for item in items:
        result += f"{BULLET}{CODE.format(item['command'])} - {item['description']}\n"
    
    return result + "\n"