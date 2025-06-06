"""
Вспомогательные функции для работы с ботом
"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from config import ROLES, ORDER_STATUSES
from database import get_user_role, get_all_users, get_technicians, get_unapproved_users

def get_status_text(status_code: str) -> str:
    """
    Возвращает текстовое представление статуса заказа
    
    Args:
        status_code: Код статуса заказа
        
    Returns:
        str: Текстовое представление статуса
    """
    status_mapping = {
        'new': '🆕 Новый',
        'assigned': '📋 Назначен',
        'in_progress': '🔧 В работе',
        'completed': '✅ Завершен',
        'cancelled': '❌ Отменен'
    }
    return status_mapping.get(status_code, f'Неизвестный ({status_code})')

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

def is_admin(user_id_or_info) -> bool:
    """
    Проверяет, является ли пользователь администратором.
    
    Args:
        user_id_or_info: может быть int (ID пользователя) или dict (словарь с информацией о пользователе)
    
    Returns:
        bool: True, если пользователь - администратор, иначе False
    """
    if isinstance(user_id_or_info, dict):
        return user_id_or_info.get('role') == 'admin'
    else:
        role = get_user_role(user_id_or_info)
        return role == 'admin'

def is_dispatcher(user_id_or_info) -> bool:
    """
    Проверяет, является ли пользователь диспетчером.
    
    Args:
        user_id_or_info: может быть int (ID пользователя) или dict (словарь с информацией о пользователе)
    
    Returns:
        bool: True, если пользователь - диспетчер, иначе False
    """
    if isinstance(user_id_or_info, dict):
        return user_id_or_info.get('role') == 'dispatcher'
    else:
        role = get_user_role(user_id_or_info)
        return role == 'dispatcher'

def is_technician(user_id_or_info) -> bool:
    """
    Проверяет, является ли пользователь мастером.
    
    Args:
        user_id_or_info: может быть int (ID пользователя) или dict (словарь с информацией о пользователе)
    
    Returns:
        bool: True, если пользователь - мастер, иначе False
    """
    if isinstance(user_id_or_info, dict):
        return user_id_or_info.get('role') == 'technician'
    else:
        role = get_user_role(user_id_or_info)
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
            InlineKeyboardButton("🔧 Заказы", callback_data="manage_orders"),
            InlineKeyboardButton("👥 Управление пользователями", callback_data="manage_users"),
            InlineKeyboardButton("📊 Логи активности", callback_data="activity_logs")
        )
    elif is_dispatcher(user_id):
        # Кнопки для диспетчеров
        keyboard.add(
            InlineKeyboardButton("🔧 Заказы", callback_data="manage_orders")
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
    Возвращает клавиатуру для изменения статуса заказа с расширенными статусами
    
    Args:
        order_id (int): ID заказа
        user_id (int, optional): ID пользователя для проверки роли
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Проверяем роль пользователя
    is_admin_user = user_id and is_admin(user_id)
    is_dispatcher_user = user_id and is_dispatcher(user_id)
    is_technician_user = user_id and is_technician(user_id)
    
    # Получаем текущий статус заказа
    order = get_order(order_id)
    current_status = order["status"] if order else "new"
    
    # Общие кнопки статусов для всех пользователей
    if current_status in ['new', 'approved']:
        # Начальные статусы для новых заказов
        keyboard.add(
            InlineKeyboardButton("✅ Принят", callback_data=f"status_{order_id}_approved"),
            InlineKeyboardButton("👨‍🔧 Назначен", callback_data=f"status_{order_id}_assigned")
        )
    
    if current_status in ['approved', 'assigned', 'scheduled']:
        # Статусы для назначенных и запланированных заказов
        keyboard.add(
            InlineKeyboardButton("📅 Запланирован", callback_data=f"status_{order_id}_scheduled"),
            InlineKeyboardButton("🔄 В работе", callback_data=f"status_{order_id}_in_progress")
        )
    
    if current_status in ['in_progress', 'pending_parts', 'pending_client', 'testing']:
        # Статусы для заказов в процессе работы
        keyboard.add(
            InlineKeyboardButton("⏳ Ожидание запчастей", callback_data=f"status_{order_id}_pending_parts"),
            InlineKeyboardButton("👥 Ожидание клиента", callback_data=f"status_{order_id}_pending_client")
        )
        keyboard.add(
            InlineKeyboardButton("🧪 Тестирование", callback_data=f"status_{order_id}_testing"),
            InlineKeyboardButton("📦 Готов к выдаче", callback_data=f"status_{order_id}_ready")
        )
    
    if current_status in ['ready', 'testing']:
        # Завершающие статусы
        keyboard.add(
            InlineKeyboardButton("✅ Завершен", callback_data=f"status_{order_id}_completed")
        )
    
    # Управленческие кнопки только для админов и диспетчеров
    if is_admin_user or is_dispatcher_user:
        management_row = []
        
        if current_status not in ['cancelled', 'completed', 'rejected']:
            management_row.append(InlineKeyboardButton("❌ Отменен", callback_data=f"status_{order_id}_cancelled"))
            management_row.append(InlineKeyboardButton("⛔ Отклонен", callback_data=f"status_{order_id}_rejected"))
        
        if management_row:
            keyboard.row(*management_row)
            
        # Дополнительный статус для особых случаев
        if current_status not in ['delayed', 'completed']:
            keyboard.add(InlineKeyboardButton("⏱ Отложен", callback_data=f"status_{order_id}_delayed"))
    
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

def get_back_to_orders_keyboard(order_id=None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками возврата к просмотру заказа или списку заказов
    
    Args:
        order_id (int, optional): ID заказа для возврата к его просмотру
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками возврата
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if order_id:
        # Кнопка возврата к конкретному заказу
        keyboard.add(InlineKeyboardButton(
            "↩️ Назад к заказу", 
            callback_data=f"delete_order_{order_id}"
        ))
    
    # Кнопка возврата к списку заказов
    keyboard.add(InlineKeyboardButton(
        "↩️ Назад к списку заказов", 
        callback_data="delete_order_menu"
    ))
    
    # Кнопка возврата в главное меню
    keyboard.add(InlineKeyboardButton(
        "↩️ Назад в главное меню", 
        callback_data="main_menu"
    ))
    
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
    
    # Формируем сообщение с учетом того, что order - это словарь
    message = f"🔔 Новый заказ #{order.get('order_id', '')}\n\n"
    # Используем функцию format_orders_list из utils.py вместо несуществующего метода format_for_display
    message += format_orders_list([order], user_role='admin')[0]
    
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
        status = order.get('status', '') if isinstance(order, dict) else order.status
        
        if status == "new":
            status_emoji = "🆕"
        elif status == "assigned":
            status_emoji = "📌"
        elif status == "in_progress":
            status_emoji = "🔧"
        elif status == "completed":
            status_emoji = "✅"
        elif status == "cancelled":
            status_emoji = "❌"
        
        # Функция для перевода статуса
        def get_status_russian(status_code):
            statuses = {
                'new': 'Новый',
                'assigned': 'Назначен',
                'in_progress': 'В работе',
                'completed': 'Выполнен',
                'cancelled': 'Отменен'
            }
            return statuses.get(status_code, 'Неизвестный статус')
            
        # Получаем значения в зависимости от типа (dict или object)
        if isinstance(order, dict):
            order_id = order.get('order_id', 'Н/Д')
            client_name = order.get('client_name', 'Н/Д')
            client_phone = order.get('client_phone', 'Н/Д')
            client_address = order.get('client_address', 'Н/Д')
            status_russian = get_status_russian(status)
        else:
            order_id = order.order_id
            client_name = order.client_name
            client_phone = order.client_phone
            client_address = order.client_address
            # Используем метод объекта, если он есть, иначе используем функцию
            status_russian = order.status_to_russian() if hasattr(order, 'status_to_russian') else get_status_russian(status)
            
        message += f"{status_emoji} Заказ #{order_id} - {status_russian}\n"
        
        # Скрываем номер телефона для мастеров
        if user_role == 'technician':
            message += f"👤 {client_name}\n"
        else:
            message += f"👤 {client_name} | 📱 {client_phone}\n"
            
        message += f"🏠 {client_address}\n"
        
        if show_buttons:
            # Используем уже полученный order_id
            keyboard.add(InlineKeyboardButton(f"Заказ #{order_id}", callback_data=f"order_{order_id}"))
        
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
        if is_admin(user):
            admins.append(user)
        elif is_dispatcher(user):
            dispatchers.append(user)
        elif is_technician(user):
            technicians.append(user)
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for user in admins + dispatchers + technicians:
        username = user.get('username', '')
        username_info = f" (@{username})" if username else ""
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        role = user.get('role', '')
        user_id = user.get('user_id', '')
        name = f"{full_name}{username_info} - {get_role_name(role)}"
        keyboard.add(InlineKeyboardButton(name, callback_data=f"delete_user_{user_id}"))
    
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
    
    # Отображаем список заказов для возможности удаления
    for order in orders:
        status_emoji = "🔄"
        status = order.get('status', '')
        if status == "new":
            status_emoji = "🆕"
        elif status == "assigned":
            status_emoji = "📌"
        elif status == "in_progress":
            status_emoji = "🔧"
        elif status == "completed":
            status_emoji = "✅"
        elif status == "cancelled":
            status_emoji = "❌"
            
        order_id = order.get('order_id', '')
        client_name = order.get('client_name', '')
        button_text = f"{status_emoji} Заказ #{order_id} - {client_name}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"delete_order_{order_id}"))
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="manage_orders"))
    
    return message, keyboard

def get_activity_logs_keyboard(page=0, filter_type=None) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для просмотра логов активности
    
    Args:
        page (int): Номер страницы для пагинации
        filter_type (str, optional): Тип фильтра для логов
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Кнопки типов фильтров
    filter_buttons = [
        InlineKeyboardButton("📝 Все", callback_data="logs_filter_all"),
        InlineKeyboardButton("➕ Заказы", callback_data="logs_filter_orders"),
        InlineKeyboardButton("👤 Пользователи", callback_data="logs_filter_users"),
        InlineKeyboardButton("🔄 Статусы", callback_data="logs_filter_statuses")
    ]
    
    # Добавляем кнопки фильтров
    keyboard.add(*filter_buttons[:2])
    keyboard.add(*filter_buttons[2:])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Пред", callback_data=f"logs_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton("🔄 Обновить", callback_data=f"logs_page_{page}"))
    nav_buttons.append(InlineKeyboardButton("➡️ След", callback_data=f"logs_page_{page+1}"))
    
    # Добавляем кнопки навигации
    if len(nav_buttons) == 3:
        keyboard.add(*nav_buttons)
    elif len(nav_buttons) == 2:
        keyboard.add(*nav_buttons)
    else:
        keyboard.add(nav_buttons[0])
    
    # Кнопка возврата
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    
    return keyboard

def format_activity_log_entry(log_entry) -> str:
    """
    Форматирует запись лога для отображения
    
    Args:
        log_entry (dict): Запись лога
    
    Returns:
        str: Форматированная запись лога
    """
    # Форматирование даты
    created_at = log_entry.get('created_at')
    if created_at:
        date_str = created_at.strftime("%d.%m.%Y %H:%M:%S")
    else:
        date_str = "Неизвестная дата"
    
    # Имя пользователя
    user_name = "Неизвестный пользователь"
    if log_entry.get('first_name'):
        user_name = log_entry.get('first_name')
        if log_entry.get('last_name'):
            user_name += f" {log_entry.get('last_name')}"
        if log_entry.get('username'):
            user_name += f" (@{log_entry.get('username')})"
    
    # Тип действия
    action_type = log_entry.get('action_type', 'unknown')
    action_type_display = {
        'order_create': 'Создание заказа',
        'order_update': 'Обновление заказа',
        'order_delete': 'Удаление заказа',
        'user_create': 'Добавление пользователя',
        'user_update': 'Обновление пользователя',
        'user_delete': 'Удаление пользователя',
        'user_approve': 'Подтверждение пользователя',
        'user_reject': 'Отклонение пользователя',
        'status_update': 'Изменение статуса заказа',
        'technician_assign': 'Назначение мастера',
        'login': 'Вход в систему',
        'unknown': 'Неизвестное действие'
    }.get(action_type, action_type)
    
    # Форматируем запись
    formatted = f"*{date_str}*\n👤 *{user_name}* ({log_entry.get('role', 'Неизвестная роль')})\n"
    formatted += f"✏️ *{action_type_display}*: {log_entry.get('action_description', 'Нет описания')}\n"
    
    # Дополнительная информация о заказе или пользователе, если есть
    if log_entry.get('client_name') and log_entry.get('related_order_id'):
        formatted += f"📝 Заказ #{log_entry.get('related_order_id')} - {log_entry.get('client_name')}\n"
    
    if log_entry.get('related_first_name') and log_entry.get('related_user_id'):
        related_user = f"{log_entry.get('related_first_name')} {log_entry.get('related_last_name') or ''}"
        if log_entry.get('related_username'):
            related_user += f" (@{log_entry.get('related_username')})"
        formatted += f"👤 Связанный пользователь: {related_user}\n"
    
    return formatted + "―――――――――――――――"
    
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