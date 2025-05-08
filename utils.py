"""
Вспомогательные функции для работы с ботом
"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from config import ROLES, ORDER_STATUSES
from database import get_user_role, get_all_users, get_technicians, get_unapproved_users

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Пытаемся импортировать из telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
except ImportError:
    # Если не получается, создаем свои классы для совместимости
    class InlineKeyboardMarkup:
        def __init__(self, row_width=3):
            self.keyboard = []
            self.row_width = row_width
            
        def add(self, *args):
            for i in range(0, len(args), self.row_width):
                self.keyboard.append(args[i:i+self.row_width])
                
    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data
    
    class ReplyKeyboardMarkup:
        def __init__(self, resize_keyboard=True, one_time_keyboard=False, row_width=3):
            self.keyboard = []
            self.resize_keyboard = resize_keyboard
            self.one_time_keyboard = one_time_keyboard
            self.row_width = row_width
            
        def add(self, *args):
            for i in range(0, len(args), self.row_width):
                self.keyboard.append(args[i:i+self.row_width])
                
    class KeyboardButton:
        def __init__(self, text):
            self.text = text
            
    class types:
        InlineKeyboardMarkup = InlineKeyboardMarkup
        InlineKeyboardButton = InlineKeyboardButton
        ReplyKeyboardMarkup = ReplyKeyboardMarkup
        KeyboardButton = KeyboardButton

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    role = get_user_role(user_id)
    return role == 'admin'

def is_dispatcher(user_id: int) -> bool:
    """Проверяет, является ли пользователь диспетчером"""
    role = get_user_role(user_id)
    return role == 'dispatcher'

def is_technician(user_id: int) -> bool:
    """Проверяет, является ли пользователь мастером"""
    role = get_user_role(user_id)
    return role == 'technician'

def get_role_name(role: str) -> str:
    """Возвращает название роли на русском языке"""
    return ROLES.get(role, role)

def get_status_name(status: str) -> str:
    """Возвращает название статуса на русском языке"""
    return ORDER_STATUSES.get(status, status)

def get_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает инлайн-клавиатуру главного меню в зависимости от роли пользователя
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка Помощь для всех пользователей
    keyboard.add(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    
    # Проверяем роль пользователя
    if is_admin(user_id):
        # Кнопки для администраторов
        keyboard.add(
            InlineKeyboardButton("📝 Все заказы", callback_data="all_orders"),
            InlineKeyboardButton("👥 Управление пользователями", callback_data="manage_users")
        )
    elif is_dispatcher(user_id):
        # Кнопки для диспетчеров
        keyboard.add(
            InlineKeyboardButton("➕ Новый заказ", callback_data="new_order"),
            InlineKeyboardButton("📋 Все заказы", callback_data="all_orders")
        )
    elif is_technician(user_id):
        # Кнопки для мастеров
        keyboard.add(
            InlineKeyboardButton("🔧 Мои заказы", callback_data="my_assigned_orders")
        )
    
    return keyboard
    
def get_reply_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру-меню с основными командами в зависимости от роли пользователя
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Добавляем общие команды
    keyboard.add(KeyboardButton("/start"), KeyboardButton("/help"))
    
    # Проверяем роль пользователя
    if is_admin(user_id):
        # Кнопки для администраторов
        keyboard.add(
            KeyboardButton("/all_orders"),
            KeyboardButton("/manage_users")
        )
    elif is_dispatcher(user_id):
        # Кнопки для диспетчеров
        keyboard.add(
            KeyboardButton("/new_order"),
            KeyboardButton("/all_orders")
        )
    elif is_technician(user_id):
        # Кнопки для мастеров
        keyboard.add(KeyboardButton("/my_assigned_orders"))
    
    return keyboard

def get_order_status_keyboard(order_id: int, user_id: int = None) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для изменения статуса заказа
    
    Args:
        order_id (int): ID заказа
        user_id (int, optional): ID пользователя для проверки роли
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Проверяем роль пользователя
    is_technician_user = user_id and is_technician(user_id)
    
    # Кнопки статусов
    keyboard.add(
        InlineKeyboardButton("🔄 В работе", callback_data=f"status_{order_id}_in_progress"),
        InlineKeyboardButton("✅ Завершен", callback_data=f"status_{order_id}_completed")
    )
    
    # Кнопка "Отменен" только для админов и диспетчеров
    if not is_technician_user:
        keyboard.add(InlineKeyboardButton("❌ Отменен", callback_data=f"status_{order_id}_cancelled"))
    
    # Кнопка "Назад"
    keyboard.add(InlineKeyboardButton("◀️ Назад к заказу", callback_data=f"order_{order_id}"))
    
    return keyboard

def get_order_management_keyboard(order_id: int, user_role: str = 'admin') -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для управления заказом
    
    Args:
        order_id (int): ID заказа
        user_role (str): Роль пользователя ('admin', 'dispatcher', 'technician')
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопку изменения статуса
    keyboard.add(InlineKeyboardButton("🔄 Изменить статус", callback_data=f"change_status_{order_id}"))
    
    # Кнопка назначения мастера только для администраторов
    if user_role == 'admin':
        keyboard.add(InlineKeyboardButton("👤 Назначить мастера", callback_data=f"assign_technician_{order_id}"))
    
    # Кнопка возврата к списку заказов
    keyboard.add(InlineKeyboardButton("◀️ Назад к списку", callback_data="all_orders"))
    
    return keyboard

def get_technician_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для мастера для управления назначенным заказом
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton("🔄 Изменить статус", callback_data=f"change_status_{order_id}"),
        InlineKeyboardButton("💰 Добавить стоимость", callback_data=f"add_cost_{order_id}"),
        InlineKeyboardButton("📝 Добавить описание работ", callback_data=f"add_description_{order_id}"),
        InlineKeyboardButton("◀️ Назад к списку", callback_data="my_assigned_orders")
    )
    
    return keyboard

def get_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру только с кнопкой возврата в главное меню
    """
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return keyboard

def get_user_management_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для управления пользователями
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton("📋 Список пользователей", callback_data="list_users"),
        InlineKeyboardButton("✅ Запросы на подтверждение", callback_data="approval_requests"),
        InlineKeyboardButton("➕ Добавить администратора", callback_data="add_admin"),
        InlineKeyboardButton("➕ Добавить диспетчера", callback_data="add_dispatcher"),
        InlineKeyboardButton("➕ Добавить мастера", callback_data="add_technician"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard

def get_approval_requests_keyboard() -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Возвращает клавиатуру для подтверждения запросов пользователей
    """
    unapproved_users = get_unapproved_users()
    
    if not unapproved_users:
        message = "📋 Запросы на подтверждение\n\nНет новых запросов на подтверждение."
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="manage_users"))
        return message, keyboard
    
    message = "📋 Запросы на подтверждение\n\n"
    for user in unapproved_users:
        username_info = f" (@{user.username})" if user.username else ""
        message += f"👤 {user.get_full_name()}{username_info} - {get_role_name(user.role)}\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for user in unapproved_users:
        name = user.get_full_name()
        if len(name) > 15:  # Укорачиваем имя для кнопки
            name = name[:12] + "..."
            
        keyboard.add(
            InlineKeyboardButton(f"✅ {name}", callback_data=f"approve_{user.user_id}"),
            InlineKeyboardButton(f"❌ {name}", callback_data=f"reject_{user.user_id}")
        )
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="manage_users"))
    
    return message, keyboard

def get_technician_list_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру со списком мастеров для назначения
    """
    technicians = get_technicians()
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for tech in technicians:
        name = tech.get_full_name()
        if len(name) > 20:  # Укорачиваем имя для кнопки
            name = name[:17] + "..."
            
        keyboard.add(InlineKeyboardButton(name, callback_data=f"assign_{order_id}_{tech.user_id}"))
    
    keyboard.add(InlineKeyboardButton("◀️ Назад к заказу", callback_data=f"order_{order_id}"))
    
    return keyboard

def send_order_notification_to_admins(bot, order_id: int) -> None:
    """
    Отправляет уведомление администраторам о новом заказе
    """
    from database import get_order
    
    # Получаем всех пользователей
    users = get_all_users()
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        return
    
    message = f"🔔 Новый заказ #{order.order_id}\n\n{order.format_for_display(user_role='admin')}"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👁️ Посмотреть заказ", callback_data=f"order_{order_id}"))
    
    # Отправляем уведомление всем администраторам
    for user in users:
        if user.is_admin():
            try:
                bot.send_message(user.user_id, message, reply_markup=keyboard)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору {user.user_id}: {e}")

def validate_phone(phone: str) -> bool:
    """
    Проверяет формат номера телефона
    """
    # Удаляем все нецифровые символы из строки
    digits_only = re.sub(r'\D', '', phone)
    
    # Проверяем длину (от 10 до 15 цифр)
    return 10 <= len(digits_only) <= 15

def format_orders_list(orders: List[Dict], show_buttons: bool = True, user_role: str = 'admin') -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Форматирует список заказов для отображения
    
    Args:
        orders: Список заказов для отображения
        show_buttons: Показывать ли кнопки для каждого заказа
        user_role: Роль пользователя ('admin', 'dispatcher', 'technician')
    """
    if not orders:
        message = "📋 Список заказов\n\nНет заказов для отображения."
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        return message, keyboard
    
    message = "📋 Список заказов\n\n"
    keyboard = None
    
    if show_buttons:
        keyboard = InlineKeyboardMarkup(row_width=2)
    
    for order in orders:
        status_emoji = "🔄"
        if order.status == "new":
            status_emoji = "🆕"
        elif order.status == "assigned":
            status_emoji = "📌"
        elif order.status == "in_progress":
            status_emoji = "🔧"
        elif order.status == "completed":
            status_emoji = "✅"
        elif order.status == "cancelled":
            status_emoji = "❌"
            
        message += f"{status_emoji} Заказ #{order.order_id} - {order.status_to_russian()}\n"
        
        # Скрываем номер телефона для мастеров
        if user_role == 'technician':
            message += f"👤 {order.client_name}\n"
        else:
            message += f"👤 {order.client_name} | 📱 {order.client_phone}\n"
            
        message += f"🏠 {order.client_address}\n"
        
        if show_buttons:
            keyboard.add(InlineKeyboardButton(f"Заказ #{order.order_id}", callback_data=f"order_{order.order_id}"))
        
        message += "\n"
    
    if show_buttons:
        keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    
    return message, keyboard