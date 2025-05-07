import re
import logging
from typing import List, Dict, Tuple, Optional
try:
    from telebot import types
except ImportError:
    # Заглушка для отладки без телебота
    class InlineKeyboardMarkup:
        def __init__(self, row_width=3):
            self.row_width = row_width
            self.keyboard = []
        
        def add(self, *args):
            self.keyboard.extend(args)
            return self
    
    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data
    
    class types:
        InlineKeyboardMarkup = InlineKeyboardMarkup
        InlineKeyboardButton = InlineKeyboardButton
from config import ROLES, ORDER_STATUSES
from database import (
    get_user_role, get_all_users, get_order, is_user_approved,
    approve_user, reject_user, get_unapproved_users
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return get_user_role(user_id) == 'admin'

def is_dispatcher(user_id: int) -> bool:
    """Проверяет, является ли пользователь диспетчером"""
    return get_user_role(user_id) == 'dispatcher'

def is_technician(user_id: int) -> bool:
    """Проверяет, является ли пользователь техником"""
    return get_user_role(user_id) == 'technician'

def get_role_name(role: str) -> str:
    """Возвращает название роли на русском языке"""
    return ROLES.get(role, role)

def get_status_name(status: str) -> str:
    """Возвращает название статуса на русском языке"""
    return ORDER_STATUSES.get(status, status)

def get_main_menu_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру главного меню в зависимости от роли пользователя
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Общие кнопки для всех пользователей
    keyboard.add(types.InlineKeyboardButton("❓ Помощь", callback_data="help"))
    
    role = get_user_role(user_id)
    
    if role == 'admin':
        # Кнопки для администратора
        keyboard.add(
            types.InlineKeyboardButton("📋 Все заказы", callback_data="all_orders"),
            types.InlineKeyboardButton("👥 Управление пользователями", callback_data="manage_users")
        )
    elif role == 'dispatcher':
        # Кнопки для диспетчера
        keyboard.add(
            types.InlineKeyboardButton("➕ Новый заказ", callback_data="new_order"),
            types.InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")
        )
    elif role == 'technician':
        # Кнопки для техника
        keyboard.add(types.InlineKeyboardButton("📋 Мои заказы", callback_data="my_assigned_orders"))
    
    return keyboard

def get_order_status_keyboard(order_id: int) -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для изменения статуса заказа
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    order = get_order(order_id)
    if not order:
        return keyboard
    
    current_status = order['status']
    
    # Добавляем кнопки для статусов, которые имеют смысл в текущем контексте
    if current_status == 'new':
        keyboard.add(types.InlineKeyboardButton("🔄 В работе", callback_data=f"status_{order_id}_in_progress"))
    elif current_status == 'assigned':
        keyboard.add(types.InlineKeyboardButton("🔄 В работе", callback_data=f"status_{order_id}_in_progress"))
    elif current_status == 'in_progress':
        keyboard.add(types.InlineKeyboardButton("✅ Завершен", callback_data=f"status_{order_id}_completed"))
    
    # Всегда добавляем кнопку отмены, если заказ не завершен и не отменен
    if current_status not in ['completed', 'cancelled']:
        keyboard.add(types.InlineKeyboardButton("❌ Отменен", callback_data=f"status_{order_id}_cancelled"))
    
    # Кнопка возврата к деталям заказа
    keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data=f"order_{order_id}"))
    
    return keyboard

def get_order_management_keyboard(order_id: int) -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для управления заказом
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    order = get_order(order_id)
    if not order:
        return keyboard
    
    current_status = order['status']
    
    # Кнопка изменения статуса доступна для всех заказов
    keyboard.add(types.InlineKeyboardButton("🔄 Изменить статус", callback_data=f"change_status_{order_id}"))
    
    # Кнопка назначения техника
    keyboard.add(types.InlineKeyboardButton("👨‍🔧 Назначить техника", callback_data=f"assign_technician_{order_id}"))
    
    # Кнопки для добавления стоимости и описания работ доступны только если заказ в работе или завершен
    if current_status in ['in_progress', 'completed']:
        keyboard.add(types.InlineKeyboardButton("💰 Добавить стоимость", callback_data=f"add_cost_{order_id}"))
        keyboard.add(types.InlineKeyboardButton("📝 Добавить описание работ", callback_data=f"add_description_{order_id}"))
    
    # Кнопка возврата к списку заказов
    keyboard.add(types.InlineKeyboardButton("↩️ Назад к заказам", callback_data="all_orders"))
    
    return keyboard

def get_technician_order_keyboard(order_id: int) -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для техника для управления назначенным заказом
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    order = get_order(order_id)
    if not order:
        return keyboard
    
    current_status = order['status']
    
    # Кнопки для техника
    if current_status == 'assigned':
        keyboard.add(types.InlineKeyboardButton("🔄 Начать работу", callback_data=f"status_{order_id}_in_progress"))
    elif current_status == 'in_progress':
        keyboard.add(types.InlineKeyboardButton("✅ Завершить работу", callback_data=f"status_{order_id}_completed"))
        keyboard.add(types.InlineKeyboardButton("💰 Добавить стоимость", callback_data=f"add_cost_{order_id}"))
        keyboard.add(types.InlineKeyboardButton("📝 Добавить описание работ", callback_data=f"add_description_{order_id}"))
    
    # Кнопка возврата к списку назначенных заказов
    keyboard.add(types.InlineKeyboardButton("↩️ Назад к заказам", callback_data="my_assigned_orders"))
    
    return keyboard

def get_back_to_main_menu_keyboard() -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру только с кнопкой возврата в главное меню
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("↩️ Главное меню", callback_data="main_menu"))
    return keyboard

def get_user_management_keyboard() -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для управления пользователями
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Получаем количество неподтвержденных пользователей
    unapproved_users = get_unapproved_users()
    unapproved_count = len(unapproved_users)
    
    # Добавляем кнопки
    keyboard.add(
        types.InlineKeyboardButton("📋 Список пользователей", callback_data="list_users"),
        types.InlineKeyboardButton(f"🔔 Запросы на подтверждение ({unapproved_count})", callback_data="approval_requests"),
        types.InlineKeyboardButton("➕ Добавить администратора", callback_data="add_admin"),
        types.InlineKeyboardButton("➕ Добавить диспетчера", callback_data="add_dispatcher"),
        types.InlineKeyboardButton("➕ Добавить техника", callback_data="add_technician"),
        types.InlineKeyboardButton("↩️ Главное меню", callback_data="main_menu")
    )
    return keyboard

def get_approval_requests_keyboard() -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    """
    Возвращает клавиатуру для подтверждения запросов пользователей
    """
    unapproved_users = get_unapproved_users()
    
    if not unapproved_users:
        return "🔔 *Список запросов на подтверждение пуст*", None
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    message = "🔔 *Запросы на подтверждение пользователей:*\n\n"
    
    for i, user in enumerate(unapproved_users):
        name = user['first_name']
        if user['last_name']:
            name += f" {user['last_name']}"
        
        username = f"@{user['username']}" if user['username'] else "без имени пользователя"
        role = get_role_name(user['role'])
        
        message += (
            f"{i+1}. *{name}* ({username})\n"
            f"   Роль: {role}\n"
            f"   ID: `{user['user_id']}`\n\n"
        )
        
        # Добавляем кнопки подтверждения и отклонения для каждого пользователя
        keyboard.add(
            types.InlineKeyboardButton(f"✅ Подтвердить {name}", callback_data=f"approve_{user['user_id']}"),
            types.InlineKeyboardButton(f"❌ Отклонить {name}", callback_data=f"reject_{user['user_id']}")
        )
    
    # Кнопка возврата в меню управления пользователями
    keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data="manage_users"))
    
    return message, keyboard

def get_technician_list_keyboard(order_id: int) -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру со списком техников для назначения
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Получаем всех техников
    technicians = [user for user in get_all_users() if user['role'] == 'technician']
    
    for tech in technicians:
        name = tech['first_name']
        if tech['last_name']:
            name += f" {tech['last_name']}"
        keyboard.add(types.InlineKeyboardButton(
            f"{name}", callback_data=f"assign_{order_id}_{tech['user_id']}"
        ))
    
    # Кнопка возврата к деталям заказа
    keyboard.add(types.InlineKeyboardButton("↩️ Назад", callback_data=f"order_{order_id}"))
    
    return keyboard

def send_order_notification_to_admins(bot, order_id: int) -> None:
    """
    Отправляет уведомление администраторам о новом заказе
    """
    order = get_order(order_id)
    if not order:
        return
    
    # Получаем всех администраторов
    admins = [user for user in get_all_users() if user['role'] == 'admin']
    
    # Формируем сообщение
    message = (
        f"⚠️ *Новый заказ #{order_id}* ⚠️\n\n"
        f"📱 Телефон: {order['client_phone']}\n"
        f"👤 Клиент: {order['client_name']}\n"
        f"🏠 Адрес: {order['client_address']}\n\n"
        f"Нажмите для просмотра деталей: /order_{order_id}"
    )
    
    # Отправляем уведомление всем администраторам
    for admin in admins:
        try:
            bot.send_message(admin['user_id'], message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администратору {admin['user_id']}: {e}")

def validate_phone(phone: str) -> bool:
    """
    Проверяет формат номера телефона
    """
    # Простая проверка: номер должен содержать только цифры, +, - и пробелы
    # и должен быть не короче 7 символов
    phone = phone.strip()
    if len(phone) < 7:
        return False
    
    # Удаляем все нецифровые символы и проверяем, что осталось хотя бы 7 цифр
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) >= 7

def format_orders_list(orders: List[Dict], show_buttons: bool = True) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    """
    Форматирует список заказов для отображения
    """
    if not orders:
        return "📋 *Список заказов пуст*", None
    
    keyboard = types.InlineKeyboardMarkup(row_width=1) if show_buttons else None
    
    message = "📋 *Список заказов:*\n\n"
    
    for i, order in enumerate(orders):
        status_text = ORDER_STATUSES.get(order['status'], order['status'])
        
        # Краткая информация о заказе
        message += (
            f"{i+1}. *Заказ #{order['order_id']}* - {status_text}\n"
            f"   📱 {order['client_phone']} - {order['client_name']}\n"
        )
        
        # Добавляем стоимость, если она указана
        if order['service_cost']:
            message += f"   💰 {order['service_cost']} руб.\n"
        
        message += "\n"
        
        # Добавляем кнопку для каждого заказа
        if show_buttons:
            keyboard.add(types.InlineKeyboardButton(
                f"Заказ #{order['order_id']} - {order['client_name']}",
                callback_data=f"order_{order['order_id']}"
            ))
    
    # Добавляем кнопку возврата в главное меню
    if show_buttons:
        keyboard.add(types.InlineKeyboardButton("↩️ Главное меню", callback_data="main_menu"))
    
    return message, keyboard