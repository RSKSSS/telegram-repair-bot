import re
from typing import List, Dict, Tuple, Optional
from database import get_user_role, get_all_users

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin"""
    role = get_user_role(user_id)
    return role == 'admin'

def get_main_menu_keyboard(user_id: int):
    """Get the main menu keyboard based on user role"""
    from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Общие кнопки для всех пользователей
    buttons = [
        [InlineKeyboardButton(text="📝 Новый заказ", callback_data="new_order")],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ]
    
    # Добавляем кнопки для админов
    if is_admin(user_id):
        admin_buttons = [
            [InlineKeyboardButton(text="👨‍💼 Управление заказами", callback_data="manage_orders")],
            [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="manage_users")]
        ]
        buttons = admin_buttons + buttons
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_order_status_keyboard(order_id: int):
    """Get keyboard for updating order status"""
    from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
    
    buttons = [
        [
            InlineKeyboardButton(text="⚙️ В работе", callback_data=f"status_{order_id}_processing"),
            InlineKeyboardButton(text="✅ Завершен", callback_data=f"status_{order_id}_completed")
        ],
        [
            InlineKeyboardButton(text="❌ Отменен", callback_data=f"status_{order_id}_cancelled")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="manage_orders")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_order_management_keyboard(order_id: int):
    """Get keyboard for order management"""
    from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
    
    buttons = [
        [
            InlineKeyboardButton(text="📊 Изменить статус", callback_data=f"change_status_{order_id}")
        ],
        [
            InlineKeyboardButton(text="💰 Добавить стоимость", callback_data=f"add_cost_{order_id}"),
            InlineKeyboardButton(text="📝 Добавить описание", callback_data=f"add_description_{order_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="manage_orders")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_main_menu_keyboard():
    """Get keyboard with only a back button to main menu"""
    from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
    
    buttons = [
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_management_keyboard():
    """Get keyboard for user management"""
    from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
    
    buttons = [
        [InlineKeyboardButton(text="👨‍💼 Добавить администратора", callback_data="add_admin")],
        [InlineKeyboardButton(text="👤 Список пользователей", callback_data="list_users")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def send_order_notification_to_admins(bot, order_id: int):
    """Send a notification to all admins about a new order"""
    from database import get_order
    
    # Получаем данные заказа
    order_data = get_order(order_id)
    if not order_data:
        return
    
    # Создаем объект Order из словаря
    from models import Order
    order = Order.from_dict(order_data)
    
    # Получаем список админов
    admins = [user for user in get_all_users() if user['role'] == 'admin']
    
    # Формируем сообщение
    message = f"🆕 <b>Новый заказ #{order_id}</b>\n\n"
    message += f"👤 Клиент: {order.client_name}\n"
    message += f"📞 Телефон: {order.client_phone}\n"
    message += f"🏠 Адрес: {order.client_address}\n\n"
    message += f"🔧 Проблема: {order.problem_description}\n"
    
    # Кнопки управления заказом
    keyboard = get_order_management_keyboard(order_id)
    
    # Отправляем уведомление всем админам
    for admin in admins:
        try:
            bot.sendMessage(
                admin['user_id'],
                message,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending notification to admin {admin['user_id']}: {e}")

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Удаляем все нецифровые символы для проверки
    clean_phone = re.sub(r'\D', '', phone)
    
    # Проверяем, что телефон содержит 10-12 цифр
    if 10 <= len(clean_phone) <= 12:
        return True
    
    return False

def format_orders_list(orders: List[Dict], show_buttons: bool = True) -> Tuple[str, Optional[dict]]:
    """Format a list of orders for display"""
    from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
    
    if not orders:
        return "У вас пока нет заказов.", get_back_to_main_menu_keyboard() if show_buttons else None
    
    # Создаем текст сообщения
    message = "<b>Список заказов:</b>\n\n"
    
    # Создаем кнопки для каждого заказа, если нужно
    buttons = []
    
    for order in orders:
        # Эмодзи статуса
        status_emoji = {
            'new': '🆕',
            'processing': '⚙️',
            'completed': '✅',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        # Добавляем информацию о заказе в сообщение
        message += f"{status_emoji} <b>Заказ #{order['order_id']}</b> - {order['client_name']}\n"
        
        # Если нужно показать кнопки, добавляем кнопку для этого заказа
        if show_buttons:
            buttons.append([InlineKeyboardButton(
                text=f"Заказ #{order['order_id']} - {order['client_name']}",
                callback_data=f"order_{order['order_id']}"
            )])
    
    # Добавляем кнопку возврата в главное меню
    if show_buttons:
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
        return message, InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return message, None