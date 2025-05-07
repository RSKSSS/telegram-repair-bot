import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext
import database as db
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Regular expressions
PHONE_REGEX = re.compile(r'^(?:\+\d{1,3})?\d{10,12}$')

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin"""
    return user_id in ADMIN_IDS or db.get_user_role(user_id) == 'admin'

def get_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get the main menu keyboard based on user role"""
    keyboard = [
        [InlineKeyboardButton("Добавить заказ", callback_data='add_order')],
        [InlineKeyboardButton("Мои заказы", callback_data='my_orders')]
    ]
    
    # Admin buttons
    if is_admin(user_id):
        keyboard.extend([
            [InlineKeyboardButton("Все заказы", callback_data='all_orders')],
            [InlineKeyboardButton("Управление пользователями", callback_data='manage_users')]
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for updating order status"""
    keyboard = [
        [
            InlineKeyboardButton("В работе", callback_data=f'status:{order_id}:processing'),
            InlineKeyboardButton("Завершен", callback_data=f'status:{order_id}:completed')
        ],
        [
            InlineKeyboardButton("Отменен", callback_data=f'status:{order_id}:cancelled'),
            InlineKeyboardButton("Назад", callback_data='all_orders')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_order_management_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for order management"""
    keyboard = [
        [InlineKeyboardButton("Изменить статус", callback_data=f'change_status:{order_id}')],
        [InlineKeyboardButton("Добавить стоимость", callback_data=f'add_cost:{order_id}')],
        [InlineKeyboardButton("Добавить описание работ", callback_data=f'add_description:{order_id}')],
        [InlineKeyboardButton("Назад", callback_data='all_orders')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with only a back button to main menu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='back_to_main')]
    ])

def get_user_management_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for user management"""
    keyboard = [
        [InlineKeyboardButton("Список пользователей", callback_data='list_users')],
        [InlineKeyboardButton("Добавить администратора", callback_data='add_admin')],
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def send_order_notification_to_admins(context: CallbackContext, order_id: int):
    """Send a notification to all admins about a new order"""
    order = db.get_order(order_id)
    if not order:
        logger.error(f"Failed to find order {order_id} for admin notification")
        return
    
    from models import Order
    order_obj = Order.from_dict(order)
    
    notification_text = (
        f"🆕 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {order['client_name']}\n"
        f"📞 <b>Телефон:</b> {order['client_phone']}\n"
        f"🏠 <b>Адрес:</b> {order['client_address']}\n\n"
        f"🔧 <b>Проблема:</b>\n{order['problem_description']}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Детали заказа", callback_data=f'view_order:{order_id}')]
    ])
    
    for admin_id in ADMIN_IDS:
        try:
            context.bot.send_message(
                chat_id=admin_id,
                text=notification_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove spaces and hyphens
    phone = re.sub(r'[\s-]', '', phone)
    return bool(PHONE_REGEX.match(phone))

def format_orders_list(orders: List[Dict], show_buttons: bool = True) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Format a list of orders for display"""
    if not orders:
        return "Заказов не найдено.", get_back_to_main_menu_keyboard() if show_buttons else None
    
    text = "<b>Список заказов:</b>\n\n"
    keyboard = []
    
    for order in orders[:10]:  # Limit to 10 orders to avoid message size limits
        status_emoji = {
            'new': '🆕',
            'processing': '⚙️',
            'completed': '✅',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        order_line = (
            f"{status_emoji} <b>Заказ #{order['order_id']}</b> - {order['client_name']} "
            f"({order['client_phone']})\n"
        )
        text += order_line
        
        if show_buttons:
            keyboard.append([InlineKeyboardButton(
                f"Заказ #{order['order_id']} - {order['client_name']}",
                callback_data=f'view_order:{order["order_id"]}'
            )])
    
    if show_buttons:
        keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data='back_to_main')])
        return text, InlineKeyboardMarkup(keyboard)
    else:
        return text, None
