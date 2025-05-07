import os
import time
import logging
import json
import re
import telepot
from typing import Dict, Any, List, Tuple, Optional

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from config import TELEGRAM_BOT_TOKEN
from database import (
    initialize_database, save_user, get_user, get_user_role, 
    get_all_users, update_user_role, save_order, update_order, 
    get_order, get_orders_by_user, get_all_orders
)
from utils import (
    is_admin, get_main_menu_keyboard, get_order_status_keyboard,
    get_order_management_keyboard, get_back_to_main_menu_keyboard,
    get_user_management_keyboard, send_order_notification_to_admins,
    validate_phone, format_orders_list
)
from models import User, Order

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
AWAITING_PHONE = 'awaiting_phone'
AWAITING_NAME = 'awaiting_name'
AWAITING_ADDRESS = 'awaiting_address'
AWAITING_PROBLEM = 'awaiting_problem'
AWAITING_USER_ID = 'awaiting_user_id'
AWAITING_COST = 'awaiting_cost'
AWAITING_DESCRIPTION = 'awaiting_description'

# Хранение состояний пользователей
user_states = {}
user_data = {}

def handle_message(msg, bot):
    """Обработчик всех входящих сообщений"""
    content_type, chat_type, chat_id = telepot.glance(msg)
    logger.info(f"Message from {chat_id}: {content_type}")
    
    user_info = msg.get('from', {})
    user_id = user_info.get('id')
    first_name = user_info.get('first_name', 'User')
    last_name = user_info.get('last_name')
    username = user_info.get('username')
    
    # Сохраняем информацию о пользователе
    if user_id:
        save_user(user_id, first_name, last_name, username)
    
    # Обрабатываем команды
    if content_type == 'text':
        text = msg['text']
        
        if text.startswith('/start'):
            handle_start_command(bot, chat_id, user_id)
        elif text.startswith('/help'):
            handle_help_command(bot, chat_id, user_id)
        elif text.startswith('/new_order'):
            handle_new_order_command(bot, chat_id, user_id)
        elif text.startswith('/my_orders'):
            handle_my_orders_command(bot, chat_id, user_id)
        elif text.startswith('/all_orders') and is_admin(user_id):
            handle_all_orders_command(bot, chat_id, user_id)
        elif text.startswith('/manage_users') and is_admin(user_id):
            handle_manage_users_command(bot, chat_id, user_id)
        else:
            # Обрабатываем текстовые сообщения в зависимости от состояния пользователя
            handle_user_input(bot, chat_id, user_id, text)

def handle_callback_query(msg, bot):
    """Обработчик callback-запросов от инлайн-кнопок"""
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    logger.info(f"Callback query from {from_id}: {query_data}")
    
    # Получаем информацию о сообщении
    chat_id = msg['message']['chat']['id']
    message_id = msg['message']['message_id']
    
    # Обрабатываем различные callback данные
    if query_data == 'new_order':
        handle_new_order_callback(bot, chat_id, from_id, message_id)
    elif query_data == 'my_orders':
        handle_my_orders_callback(bot, chat_id, from_id, message_id)
    elif query_data == 'main_menu':
        handle_main_menu_callback(bot, chat_id, from_id, message_id)
    elif query_data == 'help':
        handle_help_callback(bot, chat_id, from_id, message_id)
    elif query_data.startswith('order_'):
        order_id = int(query_data.split('_')[1])
        handle_order_detail_callback(bot, chat_id, from_id, message_id, order_id)
    elif query_data == 'manage_orders' and is_admin(from_id):
        handle_manage_orders_callback(bot, chat_id, from_id, message_id)
    elif query_data == 'manage_users' and is_admin(from_id):
        handle_manage_users_callback(bot, chat_id, from_id, message_id)
    elif query_data.startswith('change_status_') and is_admin(from_id):
        order_id = int(query_data.split('_')[2])
        handle_change_status_callback(bot, chat_id, from_id, message_id, order_id)
    elif query_data.startswith('status_') and is_admin(from_id):
        parts = query_data.split('_')
        order_id = int(parts[1])
        status = parts[2]
        handle_update_status_callback(bot, chat_id, from_id, message_id, order_id, status)
    elif query_data.startswith('add_cost_') and is_admin(from_id):
        order_id = int(query_data.split('_')[2])
        handle_add_cost_callback(bot, chat_id, from_id, message_id, order_id)
    elif query_data.startswith('add_description_') and is_admin(from_id):
        order_id = int(query_data.split('_')[2])
        handle_add_description_callback(bot, chat_id, from_id, message_id, order_id)
    elif query_data == 'add_admin' and is_admin(from_id):
        handle_add_admin_callback(bot, chat_id, from_id, message_id)
    elif query_data == 'list_users' and is_admin(from_id):
        handle_list_users_callback(bot, chat_id, from_id, message_id)
    else:
        # Неизвестный callback - просто отвечаем
        bot.answerCallbackQuery(query_id, text="Неизвестное действие")

# Обработчики команд

def handle_start_command(bot, chat_id, user_id):
    """Обработчик команды /start"""
    # Получаем информацию о пользователе
    user = get_user(user_id)
    first_name = user['first_name'] if user else 'Пользователь'
    
    # Сбрасываем состояние пользователя
    user_states[user_id] = None
    
    # Формируем клавиатуру
    keyboard = get_main_menu_keyboard(user_id)
    
    # Отправляем приветственное сообщение
    bot.sendMessage(
        chat_id,
        f'Здравствуйте, {first_name}! 👋\n\n'
        f'Добро пожаловать в сервис заказа ремонта компьютеров. 🛠️\n\n'
        f'Вы можете создать новый заказ на ремонт, посмотреть статус текущих заказов '
        f'или связаться с нашими специалистами.\n\n'
        f'Используйте меню ниже для навигации:',
        reply_markup=keyboard
    )

def handle_help_command(bot, chat_id, user_id):
    """Обработчик команды /help"""
    # Формируем текст справки
    help_text = "📋 <b>Список доступных команд:</b>\n\n"
    help_text += "/start - Начать работу с ботом\n"
    help_text += "/help - Показать эту справку\n"
    help_text += "/new_order - Создать новый заказ\n"
    help_text += "/my_orders - Посмотреть ваши заказы\n"
    
    # Добавляем команды для админов
    user_role = get_user_role(user_id)
    if user_role == 'admin':
        help_text += "\n👨‍💼 <b>Команды администратора:</b>\n"
        help_text += "/all_orders - Просмотреть все заказы\n"
        help_text += "/manage_users - Управление пользователями\n"
    
    # Формируем клавиатуру
    keyboard = get_back_to_main_menu_keyboard()
    
    # Отправляем сообщение
    bot.sendMessage(
        chat_id,
        help_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_new_order_command(bot, chat_id, user_id):
    """Обработчик команды /new_order"""
    # Переводим пользователя в состояние ожидания телефона
    user_states[user_id] = AWAITING_PHONE
    user_data[user_id] = {}
    
    # Отправляем сообщение с запросом телефона
    bot.sendMessage(
        chat_id,
        "Для создания заказа, пожалуйста, введите номер телефона для связи:"
    )

def handle_my_orders_command(bot, chat_id, user_id):
    """Обработчик команды /my_orders"""
    # Получаем заказы пользователя
    orders = get_orders_by_user(user_id)
    
    # Форматируем список заказов
    message, keyboard = format_orders_list(orders)
    
    # Отправляем сообщение
    bot.sendMessage(
        chat_id,
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_all_orders_command(bot, chat_id, user_id):
    """Обработчик команды /all_orders (только для админов)"""
    # Получаем все заказы
    orders = get_all_orders()
    
    # Форматируем список заказов
    message, keyboard = format_orders_list(orders)
    
    # Отправляем сообщение
    bot.sendMessage(
        chat_id,
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_manage_users_command(bot, chat_id, user_id):
    """Обработчик команды /manage_users (только для админов)"""
    # Формируем клавиатуру
    keyboard = get_user_management_keyboard()
    
    # Отправляем сообщение
    bot.sendMessage(
        chat_id,
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

# Обработчики callback-запросов

def handle_new_order_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса new_order"""
    # Переводим пользователя в состояние ожидания телефона
    user_states[user_id] = AWAITING_PHONE
    user_data[user_id] = {}
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        "Для создания заказа, пожалуйста, введите номер телефона для связи:"
    )

def handle_my_orders_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса my_orders"""
    # Получаем заказы пользователя
    orders = get_orders_by_user(user_id)
    
    # Форматируем список заказов
    message, keyboard = format_orders_list(orders)
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_main_menu_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса main_menu"""
    # Сбрасываем состояние пользователя
    user_states[user_id] = None
    
    # Получаем информацию о пользователе
    user = get_user(user_id)
    first_name = user['first_name'] if user else 'Пользователь'
    
    # Формируем клавиатуру
    keyboard = get_main_menu_keyboard(user_id)
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        f'Здравствуйте, {first_name}! 👋\n\n'
        f'Главное меню сервиса заказа ремонта компьютеров. 🛠️\n\n'
        f'Выберите действие:',
        reply_markup=keyboard
    )

def handle_help_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса help"""
    # Формируем текст справки
    help_text = "📋 <b>Список доступных команд:</b>\n\n"
    help_text += "/start - Начать работу с ботом\n"
    help_text += "/help - Показать эту справку\n"
    help_text += "/new_order - Создать новый заказ\n"
    help_text += "/my_orders - Посмотреть ваши заказы\n"
    
    # Добавляем команды для админов
    user_role = get_user_role(user_id)
    if user_role == 'admin':
        help_text += "\n👨‍💼 <b>Команды администратора:</b>\n"
        help_text += "/all_orders - Просмотреть все заказы\n"
        help_text += "/manage_users - Управление пользователями\n"
    
    # Формируем клавиатуру
    keyboard = get_back_to_main_menu_keyboard()
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        help_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_order_detail_callback(bot, chat_id, user_id, message_id, order_id):
    """Обработчик callback-запроса order_{order_id}"""
    # Получаем данные заказа
    order_data = get_order(order_id)
    
    if not order_data:
        # Заказ не найден
        bot.editMessageText(
            (chat_id, message_id),
            "❌ Заказ не найден",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Проверяем, что это заказ пользователя или пользователь админ
    if order_data['user_id'] != user_id and not is_admin(user_id):
        # Нет доступа
        bot.editMessageText(
            (chat_id, message_id),
            "❌ У вас нет доступа к этому заказу",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Создаем объект Order из словаря
    order = Order.from_dict(order_data)
    
    # Форматируем заказ для отображения
    order_text = order.format_for_display()
    
    # Выбираем клавиатуру в зависимости от роли пользователя
    if is_admin(user_id):
        keyboard = get_order_management_keyboard(order_id)
    else:
        keyboard = get_back_to_main_menu_keyboard()
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        order_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_manage_orders_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса manage_orders (только для админов)"""
    # Получаем все заказы
    orders = get_all_orders()
    
    # Форматируем список заказов
    message, keyboard = format_orders_list(orders)
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_manage_users_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса manage_users (только для админов)"""
    # Формируем клавиатуру
    keyboard = get_user_management_keyboard()
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_change_status_callback(bot, chat_id, user_id, message_id, order_id):
    """Обработчик callback-запроса change_status_{order_id} (только для админов)"""
    # Получаем данные заказа
    order_data = get_order(order_id)
    
    if not order_data:
        # Заказ не найден
        bot.editMessageText(
            (chat_id, message_id),
            "❌ Заказ не найден",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Формируем клавиатуру
    keyboard = get_order_status_keyboard(order_id)
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        f"Выберите новый статус для заказа #{order_id}:",
        reply_markup=keyboard
    )

def handle_update_status_callback(bot, chat_id, user_id, message_id, order_id, status):
    """Обработчик callback-запроса status_{order_id}_{status} (только для админов)"""
    # Обновляем статус заказа
    update_order(order_id, status=status)
    
    # Получаем обновленные данные заказа
    order_data = get_order(order_id)
    
    # Создаем объект Order из словаря
    order = Order.from_dict(order_data)
    
    # Форматируем заказ для отображения
    order_text = order.format_for_display()
    
    # Добавляем сообщение об успешном обновлении
    order_text += f"\n✅ Статус заказа изменен на: <b>{order.status_to_russian()}</b>"
    
    # Формируем клавиатуру
    keyboard = get_order_management_keyboard(order_id)
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        order_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    # Уведомляем клиента об изменении статуса
    try:
        client_id = order_data['user_id']
        if client_id and client_id != user_id:
            status_msg = f"🔔 <b>Статус вашего заказа #{order_id} изменен</b>\n\n"
            status_msg += f"Новый статус: <b>{order.status_to_russian()}</b>"
            
            bot.sendMessage(
                client_id,
                status_msg,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error sending notification to client: {e}")

def handle_add_cost_callback(bot, chat_id, user_id, message_id, order_id):
    """Обработчик callback-запроса add_cost_{order_id} (только для админов)"""
    # Сохраняем id заказа в данных пользователя
    user_data[user_id] = {'order_id': order_id}
    
    # Переводим пользователя в состояние ожидания стоимости
    user_states[user_id] = AWAITING_COST
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        f"Введите стоимость услуг для заказа #{order_id} (только число):"
    )

def handle_add_description_callback(bot, chat_id, user_id, message_id, order_id):
    """Обработчик callback-запроса add_description_{order_id} (только для админов)"""
    # Сохраняем id заказа в данных пользователя
    user_data[user_id] = {'order_id': order_id}
    
    # Переводим пользователя в состояние ожидания описания
    user_states[user_id] = AWAITING_DESCRIPTION
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        f"Введите описание выполненных работ для заказа #{order_id}:"
    )

def handle_add_admin_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса add_admin (только для админов)"""
    # Переводим пользователя в состояние ожидания ID пользователя
    user_states[user_id] = AWAITING_USER_ID
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        "Введите ID пользователя, которого хотите сделать администратором:"
    )

def handle_list_users_callback(bot, chat_id, user_id, message_id):
    """Обработчик callback-запроса list_users (только для админов)"""
    # Получаем список пользователей
    users = get_all_users()
    
    # Формируем сообщение
    message = "<b>Список пользователей:</b>\n\n"
    
    for user in users:
        role_emoji = "👨‍💼" if user['role'] == 'admin' else "👤"
        message += f"{role_emoji} <b>ID:</b> {user['user_id']}\n"
        message += f"   <b>Имя:</b> {user['first_name']}"
        if user['last_name']:
            message += f" {user['last_name']}"
        if user['username']:
            message += f" (@{user['username']})"
        message += f"\n   <b>Роль:</b> {user['role']}\n\n"
    
    # Формируем клавиатуру
    keyboard = get_user_management_keyboard()
    
    # Изменяем сообщение
    bot.editMessageText(
        (chat_id, message_id),
        message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

# Обработчики пользовательского ввода

def handle_user_input(bot, chat_id, user_id, text):
    """Обработка пользовательского ввода в зависимости от состояния"""
    state = user_states.get(user_id)
    
    if state == AWAITING_PHONE:
        handle_phone_input(bot, chat_id, user_id, text)
    elif state == AWAITING_NAME:
        handle_name_input(bot, chat_id, user_id, text)
    elif state == AWAITING_ADDRESS:
        handle_address_input(bot, chat_id, user_id, text)
    elif state == AWAITING_PROBLEM:
        handle_problem_input(bot, chat_id, user_id, text)
    elif state == AWAITING_USER_ID:
        handle_user_id_input(bot, chat_id, user_id, text)
    elif state == AWAITING_COST:
        handle_cost_input(bot, chat_id, user_id, text)
    elif state == AWAITING_DESCRIPTION:
        handle_description_input(bot, chat_id, user_id, text)
    else:
        # Если нет активного состояния, просто отвечаем сообщением
        bot.sendMessage(
            chat_id,
            "Для начала работы с ботом используйте команду /start или выберите действие в меню.",
            reply_markup=get_main_menu_keyboard(user_id)
        )

def handle_phone_input(bot, chat_id, user_id, text):
    """Обработка ввода телефона"""
    if not validate_phone(text):
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, введите корректный номер телефона (должен содержать от 10 до 12 цифр)."
        )
        return
    
    # Сохраняем телефон
    user_data[user_id]['client_phone'] = text
    
    # Меняем состояние
    user_states[user_id] = AWAITING_NAME
    
    # Отправляем следующий запрос
    bot.sendMessage(
        chat_id,
        "Введите ваше имя и фамилию:"
    )

def handle_name_input(bot, chat_id, user_id, text):
    """Обработка ввода имени"""
    if len(text.strip()) < 3:
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, введите корректное имя (минимум 3 символа)."
        )
        return
    
    # Сохраняем имя
    user_data[user_id]['client_name'] = text
    
    # Меняем состояние
    user_states[user_id] = AWAITING_ADDRESS
    
    # Отправляем следующий запрос
    bot.sendMessage(
        chat_id,
        "Введите ваш адрес (город, улица, дом, квартира):"
    )

def handle_address_input(bot, chat_id, user_id, text):
    """Обработка ввода адреса"""
    if len(text.strip()) < 5:
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, введите корректный адрес (минимум 5 символов)."
        )
        return
    
    # Сохраняем адрес
    user_data[user_id]['client_address'] = text
    
    # Меняем состояние
    user_states[user_id] = AWAITING_PROBLEM
    
    # Отправляем следующий запрос
    bot.sendMessage(
        chat_id,
        "Опишите проблему с вашим компьютером:"
    )

def handle_problem_input(bot, chat_id, user_id, text):
    """Обработка ввода описания проблемы"""
    if len(text.strip()) < 10:
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, опишите проблему более подробно (минимум 10 символов)."
        )
        return
    
    # Сохраняем описание проблемы
    user_data[user_id]['problem_description'] = text
    
    # Создаем заказ
    order_id = save_order(
        user_id,
        user_data[user_id]['client_phone'],
        user_data[user_id]['client_name'],
        user_data[user_id]['client_address'],
        user_data[user_id]['problem_description']
    )
    
    # Отправляем подтверждение
    bot.sendMessage(
        chat_id,
        f"✅ Ваш заказ #{order_id} успешно создан!\n\n"
        f"Наши специалисты свяжутся с вами в ближайшее время для уточнения деталей.",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    
    # Сбрасываем состояние
    user_states[user_id] = None
    
    # Отправляем уведомление админам
    send_order_notification_to_admins(bot, order_id)

def handle_user_id_input(bot, chat_id, user_id, text):
    """Обработка ввода ID пользователя для назначения администратором"""
    try:
        new_admin_id = int(text.strip())
        
        # Проверяем, существует ли пользователь
        user = get_user(new_admin_id)
        if not user:
            bot.sendMessage(
                chat_id,
                "⚠️ Пользователь с таким ID не найден в базе данных. "
                "Пользователь должен сначала взаимодействовать с ботом.",
                reply_markup=get_user_management_keyboard()
            )
            user_states[user_id] = None
            return
        
        # Назначаем пользователя администратором
        update_user_role(new_admin_id, 'admin')
        
        # Отправляем подтверждение
        bot.sendMessage(
            chat_id,
            f"✅ Пользователь {user['first_name']} (ID: {new_admin_id}) "
            f"успешно назначен администратором.",
            reply_markup=get_user_management_keyboard()
        )
        
        # Уведомляем нового администратора
        try:
            bot.sendMessage(
                new_admin_id,
                "🎉 Поздравляем! Вам были предоставлены права администратора. "
                "Теперь вам доступны дополнительные функции бота.",
                reply_markup=get_main_menu_keyboard(new_admin_id)
            )
        except Exception as e:
            logger.error(f"Error sending notification to new admin: {e}")
    
    except ValueError:
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, введите корректный ID пользователя (только цифры).",
            reply_markup=get_user_management_keyboard()
        )
    
    # Сбрасываем состояние
    user_states[user_id] = None

def handle_cost_input(bot, chat_id, user_id, text):
    """Обработка ввода стоимости услуг"""
    try:
        # Пытаемся преобразовать ввод в число
        cost = float(text.strip().replace(',', '.'))
        
        # Проверяем, что стоимость положительная
        if cost <= 0:
            raise ValueError("Стоимость должна быть положительной")
        
        # Получаем ID заказа
        order_id = user_data[user_id]['order_id']
        
        # Обновляем заказ
        update_order(order_id, service_cost=cost)
        
        # Получаем обновленные данные заказа
        order_data = get_order(order_id)
        order = Order.from_dict(order_data)
        
        # Отправляем подтверждение
        bot.sendMessage(
            chat_id,
            f"✅ Стоимость для заказа #{order_id} успешно установлена: {cost} руб.",
            reply_markup=get_order_management_keyboard(order_id)
        )
        
        # Уведомляем клиента
        try:
            client_id = order_data['user_id']
            if client_id and client_id != user_id:
                cost_msg = f"🔔 <b>Обновление по заказу #{order_id}</b>\n\n"
                cost_msg += f"Стоимость услуг: <b>{cost} руб.</b>"
                
                bot.sendMessage(
                    client_id,
                    cost_msg,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error sending notification to client: {e}")
    
    except ValueError:
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, введите корректную стоимость (только число)."
        )
        return
    
    # Сбрасываем состояние
    user_states[user_id] = None

def handle_description_input(bot, chat_id, user_id, text):
    """Обработка ввода описания выполненных работ"""
    if len(text.strip()) < 5:
        bot.sendMessage(
            chat_id,
            "⚠️ Пожалуйста, введите более подробное описание работ (минимум 5 символов)."
        )
        return
    
    # Получаем ID заказа
    order_id = user_data[user_id]['order_id']
    
    # Обновляем заказ
    update_order(order_id, service_description=text)
    
    # Получаем обновленные данные заказа
    order_data = get_order(order_id)
    
    # Отправляем подтверждение
    bot.sendMessage(
        chat_id,
        f"✅ Описание для заказа #{order_id} успешно добавлено.",
        reply_markup=get_order_management_keyboard(order_id)
    )
    
    # Уведомляем клиента
    try:
        client_id = order_data['user_id']
        if client_id and client_id != user_id:
            desc_msg = f"🔔 <b>Обновление по заказу #{order_id}</b>\n\n"
            desc_msg += f"Добавлено описание выполненных работ:\n{text}"
            
            bot.sendMessage(
                client_id,
                desc_msg,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error sending notification to client: {e}")
    
    # Сбрасываем состояние
    user_states[user_id] = None

def setup_handlers(bot):
    """Настройка обработчиков сообщений и callback-запросов"""
    return {
        'chat': lambda msg: handle_message(msg, bot),
        'callback_query': lambda msg: handle_callback_query(msg, bot)
    }