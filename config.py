import os

# Токен Telegram бота
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Настройки базы данных
DATABASE_URL = os.environ.get('DATABASE_URL')

# Роли пользователей
ROLES = {
    'dispatcher': 'Диспетчер',
    'technician': 'Техник',
    'admin': 'Администратор'
}

# Статусы заказов
ORDER_STATUSES = {
    'new': 'Новый',
    'assigned': 'Назначен',
    'in_progress': 'В работе',
    'completed': 'Завершен',
    'cancelled': 'Отменен'
}