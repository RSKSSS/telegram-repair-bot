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
            InlineKeyboardButton("👥 Управление пользователями", callback_data="manage_users"),
            InlineKeyboardButton("❌ Удаление заказов", callback_data="manage_orders")
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
        InlineKeyboardButton("❌ Удалить пользователя", callback_data="delete_user_menu"),
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
                
def send_order_status_update_notification(bot, order_id: int, old_status: str, new_status: str) -> None:
    """
    Отправляет уведомление главному администратору об изменении статуса заказа
    
    Args:
        bot: Экземпляр бота
        order_id: ID заказа
        old_status: Предыдущий статус заказа
        new_status: Новый статус заказа
    """
    from database import get_order
    
    # Получаем всех пользователей
    users = get_all_users()
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        logger.error(f"Не удалось получить информацию о заказе {order_id} для отправки уведомления об изменении статуса.")
        return
    
    # Находим главного администратора (первого зарегистрированного)
    admins = [user for user in users if user.is_admin()]
    
    if not admins:
        logger.warning("В системе нет администраторов для отправки уведомления об изменении статуса заказа.")
        return
        
    main_admin = admins[0]  # Берем первого администратора как главного
    
    # Получаем названия статусов на русском языке
    old_status_name = get_status_name(old_status)
    new_status_name = get_status_name(new_status)
    
    # Формируем текст уведомления
    message = (
        f"🔄 *Изменение статуса заказа #{order_id}*\n\n"
        f"👤 Клиент: {order.client_name}\n"
        f"📞 Телефон: {order.client_phone}\n\n"
        f"Статус изменен: *{old_status_name}* → *{new_status_name}*\n\n"
        f"🔍 Проблема: {order.problem_description}\n"
    )
    
    # Создаем инлайн клавиатуру с кнопкой просмотра заказа
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👁️ Посмотреть заказ", callback_data=f"order_{order_id}"))
    
    try:
        bot.send_message(main_admin.user_id, message, parse_mode="Markdown", reply_markup=keyboard)
        logger.info(f"Уведомление об изменении статуса заказа #{order_id} отправлено главному администратору {main_admin.user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об изменении статуса заказа #{order_id} главному администратору {main_admin.user_id}: {e}")

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
    
def get_user_list_for_deletion() -> Tuple[str, InlineKeyboardMarkup]:
    """
    Возвращает клавиатуру со списком пользователей для удаления
    """
    users = get_all_users()
    
    # Формируем сообщение со списком пользователей
    message = "❌ *Выберите пользователя для удаления*\n\n"
    message += "⚠️ **Внимание!** При удалении пользователя также будут удалены все его заказы, назначения и шаблоны.\n\n"
    
    # Сортируем пользователей по ролям
    admins = []
    dispatchers = []
    technicians = []
    
    for user in users:
        if user.is_admin():
            admins.append(user)
        elif user.is_dispatcher():
            dispatchers.append(user)
        elif user.is_technician():
            technicians.append(user)
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for user in admins + dispatchers + technicians:
        username_info = f" (@{user.username})" if user.username else ""
        name = f"{user.get_full_name()}{username_info} - {get_role_name(user.role)}"
        keyboard.add(InlineKeyboardButton(name, callback_data=f"delete_user_{user.user_id}"))
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="manage_users"))
    
    return message, keyboard
    
def get_order_list_for_deletion() -> Tuple[str, InlineKeyboardMarkup]:
    """
    Возвращает клавиатуру со списком заказов для удаления
    """
    from database import get_all_orders
    orders = get_all_orders()
    
    if not orders:
        message = "❌ *Удаление заказов*\n\nНет заказов для удаления."
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="manage_orders"))
        return message, keyboard
    
    message = "❌ *Выберите заказ для удаления*\n\n"
    message += "⚠️ **Внимание!** При удалении заказа также будут удалены все его назначения мастерам.\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Сортируем заказы по статусам и дате создания (от новых к старым)
    for order in sorted(orders, key=lambda x: (x.status != 'new', x.status != 'assigned', 
                                               x.status != 'in_progress', x.status != 'completed', 
                                               x.status != 'cancelled', -int(x.order_id))):
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
            
        button_text = f"{status_emoji} Заказ #{order.order_id} - {order.client_name}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"delete_order_{order.order_id}"))
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="manage_orders"))
    
    return message, keyboard