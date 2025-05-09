"""
Файл с конфигурацией и константами для бота
"""

# Роли пользователей
ROLES = {
    'admin': 'Администратор',
    'dispatcher': 'Диспетчер',
    'technician': 'Мастер'
}

# Статусы заказов
ORDER_STATUSES = {
    'new': 'Новый',
    'approved': 'Принят',
    'assigned': 'Назначен',
    'scheduled': 'Запланирован',
    'in_progress': 'В работе',
    'pending_parts': 'Ожидание запчастей',
    'pending_client': 'Ожидание клиента',
    'testing': 'Тестирование',
    'ready': 'Готов к выдаче',
    'completed': 'Завершен',
    'cancelled': 'Отменен',
    'rejected': 'Отклонен',
    'delayed': 'Отложен'
}

# Группы статусов для удобства фильтрации
ORDER_STATUS_GROUPS = {
    'active': ['new', 'approved', 'assigned', 'scheduled', 'in_progress', 'pending_parts', 'pending_client', 'testing'],
    'completed': ['ready', 'completed'],
    'problem': ['cancelled', 'rejected', 'delayed']
}

# Цвета для статусов
ORDER_STATUS_COLORS = {
    'new': '#FFEB3B',         # Желтый
    'approved': '#CDDC39',    # Лаймовый
    'assigned': '#8BC34A',    # Светло-зеленый
    'scheduled': '#4CAF50',   # Зеленый
    'in_progress': '#009688', # Сине-зеленый
    'pending_parts': '#FF9800', # Оранжевый
    'pending_client': '#FF5722', # Темно-оранжевый
    'testing': '#03A9F4',     # Голубой
    'ready': '#3F51B5',       # Индиго
    'completed': '#4CAF50',   # Зеленый
    'cancelled': '#F44336',   # Красный
    'rejected': '#D32F2F',    # Темно-красный
    'delayed': '#9C27B0'      # Фиолетовый
}