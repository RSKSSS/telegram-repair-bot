import logging
import re
from typing import Dict, Any, Union

# Import using python-telegram-bot instead of telegram
try:
    # Try to use the python-telegram-bot package
    from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler
    from telegram.ext import Filters, ConversationHandler, CallbackContext
    from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
except ImportError:
    # Fallback for potential import errors
    raise ImportError("Could not import from python-telegram-bot. Please install with: pip install python-telegram-bot==13.7")

import database as db
import utils
from config import TOKEN, logger, ADMIN_IDS
from models import User, Order

# Conversation states
(
    MAIN_MENU, ADD_ORDER, INPUT_PHONE, INPUT_NAME, INPUT_ADDRESS, INPUT_PROBLEM,
    MANAGE_USERS, ADD_ADMIN, LIST_USERS, WAITING_FOR_USER_ID,
    VIEW_ORDER, CHANGE_STATUS, ADD_COST, ADD_DESCRIPTION, WAITING_FOR_COST,
    WAITING_FOR_DESCRIPTION, WAITING_FOR_STATUS
) = range(17)

def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and display main menu"""
    user = update.effective_user
    user_id = user.id
    
    # Save user to database
    db.save_user(
        user_id=user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )
    
    # Check if we have any admins, if not and this is the first user, make them admin
    if not ADMIN_IDS and not db.get_all_users():
        db.update_user_role(user_id, 'admin')
        logger.info(f"Set first user {user_id} as admin")
    
    keyboard = utils.get_main_menu_keyboard(user_id)
    
    update.message.reply_text(
        f'Здравствуйте, {user.first_name}! Добро пожаловать в сервис управления ремонтом компьютеров.',
        reply_markup=keyboard
    )
    
    return MAIN_MENU

def menu_handler(update: Update, context: CallbackContext) -> int:
    """Handle menu button callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not query:
        return MAIN_MENU
    
    query.answer()
    data = query.data
    
    if data == 'add_order':
        query.edit_message_text(
            "Пожалуйста, введите номер телефона клиента (в формате +7XXXXXXXXXX):"
        )
        return INPUT_PHONE
    
    elif data == 'my_orders':
        orders = db.get_orders_by_user(user_id)
        text, markup = utils.format_orders_list(orders)
        query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return MAIN_MENU
    
    elif data == 'all_orders' and utils.is_admin(user_id):
        orders = db.get_all_orders()
        text, markup = utils.format_orders_list(orders)
        query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return MAIN_MENU
    
    elif data == 'manage_users' and utils.is_admin(user_id):
        keyboard = utils.get_user_management_keyboard()
        query.edit_message_text("Управление пользователями:", reply_markup=keyboard)
        return MANAGE_USERS
    
    elif data == 'back_to_main':
        keyboard = utils.get_main_menu_keyboard(user_id)
        query.edit_message_text(
            'Главное меню:', 
            reply_markup=keyboard
        )
        return MAIN_MENU
    
    elif data.startswith('view_order:'):
        order_id = int(data.split(':')[1])
        order = db.get_order(order_id)
        
        if not order:
            query.edit_message_text("Заказ не найден.", reply_markup=utils.get_back_to_main_menu_keyboard())
            return MAIN_MENU
        
        order_obj = Order.from_dict(order)
        order_text = order_obj.format_for_display()
        
        if utils.is_admin(user_id):
            keyboard = utils.get_order_management_keyboard(order_id)
            query.edit_message_text(order_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            return VIEW_ORDER
        else:
            query.edit_message_text(
                order_text, 
                reply_markup=utils.get_back_to_main_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )
            return MAIN_MENU
    
    return MAIN_MENU

def input_phone(update: Update, context: CallbackContext) -> int:
    """Process phone number input"""
    phone = update.message.text.strip()
    
    if not utils.validate_phone(phone):
        update.message.reply_text(
            "Неверный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX:"
        )
        return INPUT_PHONE
    
    context.user_data['phone'] = phone
    update.message.reply_text("Введите имя клиента:")
    return INPUT_NAME

def input_name(update: Update, context: CallbackContext) -> int:
    """Process name input"""
    name = update.message.text.strip()
    
    if not name:
        update.message.reply_text("Имя не может быть пустым. Пожалуйста, введите имя клиента:")
        return INPUT_NAME
    
    context.user_data['name'] = name
    update.message.reply_text("Введите адрес клиента (город, улица, дом):")
    return INPUT_ADDRESS

def input_address(update: Update, context: CallbackContext) -> int:
    """Process address input"""
    address = update.message.text.strip()
    
    if not address:
        update.message.reply_text("Адрес не может быть пустым. Пожалуйста, введите адрес:")
        return INPUT_ADDRESS
    
    context.user_data['address'] = address
    update.message.reply_text("Опишите проблему с компьютером:")
    return INPUT_PROBLEM

def input_problem(update: Update, context: CallbackContext) -> int:
    """Process problem description input and create the order"""
    problem = update.message.text.strip()
    
    if not problem:
        update.message.reply_text("Описание проблемы не может быть пустым. Пожалуйста, опишите проблему:")
        return INPUT_PROBLEM
    
    user_id = update.effective_user.id
    phone = context.user_data['phone']
    name = context.user_data['name']
    address = context.user_data['address']
    
    # Save the order to the database
    order_id = db.save_order(user_id, phone, name, address, problem)
    
    # Send notification to admins
    utils.send_order_notification_to_admins(context, order_id)
    
    # Show confirmation to the user
    keyboard = utils.get_main_menu_keyboard(user_id)
    update.message.reply_text(
        f"Заказ #{order_id} успешно создан!\n\n"
        f"Клиент: {name}\n"
        f"Телефон: {phone}\n"
        f"Адрес: {address}\n"
        f"Проблема: {problem}\n\n"
        f"Наш специалист свяжется с вами в ближайшее время.",
        reply_markup=keyboard
    )
    
    # Clear user data
    context.user_data.clear()
    
    return MAIN_MENU

def manage_users_handler(update: Update, context: CallbackContext) -> int:
    """Handle user management options"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not query or not utils.is_admin(user_id):
        return MAIN_MENU
    
    query.answer()
    data = query.data
    
    if data == 'list_users':
        users = db.get_all_users()
        
        if not users:
            query.edit_message_text(
                "Пользователей не найдено.",
                reply_markup=utils.get_user_management_keyboard()
            )
            return MANAGE_USERS
        
        text = "<b>Список пользователей:</b>\n\n"
        
        for user in users:
            role_emoji = "👤" if user['role'] == 'client' else "👑"
            text += f"{role_emoji} ID: {user['user_id']} - "
            
            if user['username']:
                text += f"@{user['username']}"
            else:
                text += f"{user['first_name']}"
                
            if user['last_name']:
                text += f" {user['last_name']}"
                
            text += f" ({user['role']})\n"
        
        query.edit_message_text(
            text,
            reply_markup=utils.get_user_management_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return MANAGE_USERS
    
    elif data == 'add_admin':
        query.edit_message_text(
            "Введите ID пользователя, которого вы хотите сделать администратором:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data='manage_users')]
            ])
        )
        return WAITING_FOR_USER_ID
    
    elif data == 'manage_users':
        keyboard = utils.get_user_management_keyboard()
        query.edit_message_text("Управление пользователями:", reply_markup=keyboard)
        return MANAGE_USERS
    
    return MANAGE_USERS

def process_user_id(update: Update, context: CallbackContext) -> int:
    """Process user ID for adding an admin"""
    if not utils.is_admin(update.effective_user.id):
        return MAIN_MENU
    
    try:
        user_id = int(update.message.text.strip())
        user = db.get_user(user_id)
        
        if not user:
            keyboard = utils.get_user_management_keyboard()
            update.message.reply_text(
                "Пользователь не найден. Пользователь должен хотя бы раз воспользоваться ботом.",
                reply_markup=keyboard
            )
            return MANAGE_USERS
        
        db.update_user_role(user_id, 'admin')
        
        keyboard = utils.get_user_management_keyboard()
        update.message.reply_text(
            f"Пользователь {user['first_name']} (ID: {user_id}) теперь администратор.",
            reply_markup=keyboard
        )
        return MANAGE_USERS
        
    except ValueError:
        keyboard = utils.get_user_management_keyboard()
        update.message.reply_text(
            "Неверный формат ID. Пожалуйста, введите числовой ID пользователя.",
            reply_markup=keyboard
        )
        return MANAGE_USERS

def order_management_handler(update: Update, context: CallbackContext) -> int:
    """Handle order management operations"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not query or not utils.is_admin(user_id):
        return MAIN_MENU
    
    query.answer()
    data = query.data
    
    if data.startswith('change_status:'):
        order_id = int(data.split(':')[1])
        keyboard = utils.get_order_status_keyboard(order_id)
        query.edit_message_text(
            f"Выберите новый статус для заказа #{order_id}:",
            reply_markup=keyboard
        )
        return CHANGE_STATUS
    
    elif data.startswith('status:'):
        _, order_id, status = data.split(':')
        order_id = int(order_id)
        
        db.update_order(order_id, status=status)
        order = db.get_order(order_id)
        
        if order:
            order_obj = Order.from_dict(order)
            order_text = order_obj.format_for_display()
            
            keyboard = utils.get_order_management_keyboard(order_id)
            query.edit_message_text(
                f"Статус заказа обновлен.\n\n{order_text}",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            query.edit_message_text(
                "Заказ не найден.",
                reply_markup=utils.get_back_to_main_menu_keyboard()
            )
        
        return VIEW_ORDER
    
    elif data.startswith('add_cost:'):
        order_id = int(data.split(':')[1])
        context.user_data['current_order_id'] = order_id
        
        query.edit_message_text(
            f"Введите стоимость услуг для заказа #{order_id} (только число):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data=f'view_order:{order_id}')]
            ])
        )
        return WAITING_FOR_COST
    
    elif data.startswith('add_description:'):
        order_id = int(data.split(':')[1])
        context.user_data['current_order_id'] = order_id
        
        query.edit_message_text(
            f"Введите описание выполненных работ для заказа #{order_id}:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data=f'view_order:{order_id}')]
            ])
        )
        return WAITING_FOR_DESCRIPTION
    
    return VIEW_ORDER

def process_cost(update: Update, context: CallbackContext) -> int:
    """Process cost input for an order"""
    if not utils.is_admin(update.effective_user.id):
        return MAIN_MENU
    
    order_id = context.user_data.get('current_order_id')
    if not order_id:
        update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново.",
            reply_markup=utils.get_back_to_main_menu_keyboard()
        )
        return MAIN_MENU
    
    try:
        cost = float(update.message.text.strip())
        if cost < 0:
            raise ValueError("Стоимость не может быть отрицательной")
        
        db.update_order(order_id, service_cost=cost)
        order = db.get_order(order_id)
        
        if order:
            order_obj = Order.from_dict(order)
            order_text = order_obj.format_for_display()
            
            keyboard = utils.get_order_management_keyboard(order_id)
            update.message.reply_text(
                f"Стоимость услуг обновлена.\n\n{order_text}",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            update.message.reply_text(
                "Заказ не найден.",
                reply_markup=utils.get_back_to_main_menu_keyboard()
            )
        
        return VIEW_ORDER
        
    except ValueError:
        update.message.reply_text(
            "Неверный формат стоимости. Пожалуйста, введите число:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data=f'view_order:{order_id}')]
            ])
        )
        return WAITING_FOR_COST

def process_description(update: Update, context: CallbackContext) -> int:
    """Process service description input for an order"""
    if not utils.is_admin(update.effective_user.id):
        return MAIN_MENU
    
    order_id = context.user_data.get('current_order_id')
    if not order_id:
        update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново.",
            reply_markup=utils.get_back_to_main_menu_keyboard()
        )
        return MAIN_MENU
    
    description = update.message.text.strip()
    if not description:
        update.message.reply_text(
            "Описание не может быть пустым. Пожалуйста, введите описание работ:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Отмена", callback_data=f'view_order:{order_id}')]
            ])
        )
        return WAITING_FOR_DESCRIPTION
    
    db.update_order(order_id, service_description=description)
    order = db.get_order(order_id)
    
    if order:
        order_obj = Order.from_dict(order)
        order_text = order_obj.format_for_display()
        
        keyboard = utils.get_order_management_keyboard(order_id)
        update.message.reply_text(
            f"Описание работ обновлено.\n\n{order_text}",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        update.message.reply_text(
            "Заказ не найден.",
            reply_markup=utils.get_back_to_main_menu_keyboard()
        )
    
    return VIEW_ORDER

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update.effective_message:
        error_message = "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова или обратитесь к администратору."
        update.effective_message.reply_text(error_message)

def setup_bot():
    """Setup the bot with all handlers"""
    # Initialize the database
    db.initialize_database()
    
    # Create the Updater
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(menu_handler)
            ],
            INPUT_PHONE: [
                MessageHandler(Filters.text & ~Filters.command, input_phone)
            ],
            INPUT_NAME: [
                MessageHandler(Filters.text & ~Filters.command, input_name)
            ],
            INPUT_ADDRESS: [
                MessageHandler(Filters.text & ~Filters.command, input_address)
            ],
            INPUT_PROBLEM: [
                MessageHandler(Filters.text & ~Filters.command, input_problem)
            ],
            MANAGE_USERS: [
                CallbackQueryHandler(manage_users_handler)
            ],
            WAITING_FOR_USER_ID: [
                MessageHandler(Filters.text & ~Filters.command, process_user_id),
                CallbackQueryHandler(manage_users_handler)
            ],
            VIEW_ORDER: [
                CallbackQueryHandler(order_management_handler)
            ],
            CHANGE_STATUS: [
                CallbackQueryHandler(order_management_handler)
            ],
            WAITING_FOR_COST: [
                MessageHandler(Filters.text & ~Filters.command, process_cost),
                CallbackQueryHandler(order_management_handler)
            ],
            WAITING_FOR_DESCRIPTION: [
                MessageHandler(Filters.text & ~Filters.command, process_description),
                CallbackQueryHandler(order_management_handler)
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
        ],
        allow_reentry=True,
        per_message=False
    )
    
    # Add handlers
    dispatcher.add_handler(conv_handler)
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    return updater
