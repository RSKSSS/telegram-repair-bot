#!/usr/bin/env python3
import logging
import os
from typing import Dict, List, Optional
import telebot
from telebot.types import Message, CallbackQuery
from telebot import TeleBot

from database import (
    save_user, get_user, get_user_role, get_all_users, get_technicians,
    update_user_role, get_all_orders, get_orders_by_user, get_assigned_orders,
    save_order, update_order, get_order, assign_order, get_order_technicians,
    approve_user, reject_user, is_user_approved, get_unapproved_users
)
from models import User, Order, Assignment
from utils import (
    is_admin, is_dispatcher, is_technician, get_role_name, get_status_name,
    get_main_menu_keyboard, get_order_status_keyboard, get_order_management_keyboard,
    get_technician_order_keyboard, get_back_to_main_menu_keyboard,
    get_user_management_keyboard, get_technician_list_keyboard,
    send_order_notification_to_admins, validate_phone, format_orders_list,
    get_approval_requests_keyboard
)

# Получаем токен бота из переменных окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Не указан токен Telegram бота. Установите переменную окружения TELEGRAM_BOT_TOKEN.")

# Инициализируем бота
bot = TeleBot(TOKEN)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения текущего состояния пользователя
user_states = {}
# Словарь для хранения текущего ID заказа в процессе ввода данных
user_order_ids = {}


def set_user_state(user_id: int, state: str, order_id: Optional[int] = None) -> None:
    """
    Устанавливает состояние пользователя
    """
    user_states[user_id] = state
    if order_id is not None:
        user_order_ids[user_id] = order_id


def clear_user_state(user_id: int) -> None:
    """
    Очищает состояние пользователя
    """
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_order_ids:
        del user_order_ids[user_id]


def get_user_state(user_id: int) -> Optional[str]:
    """
    Возвращает текущее состояние пользователя
    """
    return user_states.get(user_id)


def get_current_order_id(user_id: int) -> Optional[int]:
    """
    Возвращает ID текущего заказа пользователя
    """
    return user_order_ids.get(user_id)


# Обработчики команд
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    """
    Обработчик команды /start
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    
    # Сохраняем информацию о пользователе
    save_user(user_id, first_name, last_name, username)
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "👋 Добро пожаловать в бот сервиса ремонта компьютеров!\n\n"
            "Ваша учетная запись ожидает подтверждения администратором. "
            "Вы получите уведомление, когда ваша учетная запись будет активирована.",
            parse_mode='Markdown'
        )
        return
    
    # Приветственное сообщение
    bot.send_message(
        user_id,
        "👋 Добро пожаловать в бот сервиса ремонта компьютеров!\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help'])
def handle_help_command(message):
    """
    Обработчик команды /help
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Получаем роль пользователя для отображения соответствующей справки
    role = get_user_role(user_id)
    
    # Базовая справка для всех пользователей
    help_text = (
        "🔍 *Справка по использованию бота*\n\n"
        "Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
    )
    
    # Добавляем специфичную для роли справку
    if role == 'admin':
        help_text += (
            "*Команды для администратора:*\n"
            "/all_orders - Просмотр всех заказов\n"
            "/manage_users - Управление пользователями\n"
            "/order_<id> - Просмотр конкретного заказа по его ID\n\n"
            "Как администратор, вы можете подтверждать новых пользователей, "
            "управлять заказами и назначать техников на заказы."
        )
    elif role == 'dispatcher':
        help_text += (
            "*Команды для диспетчера:*\n"
            "/new_order - Создать новый заказ\n"
            "/my_orders - Просмотр ваших заказов\n"
            "/order_<id> - Просмотр конкретного заказа по его ID\n\n"
            "Как диспетчер, вы можете создавать новые заказы и отслеживать их выполнение."
        )
    elif role == 'technician':
        help_text += (
            "*Команды для техника:*\n"
            "/my_assigned_orders - Просмотр назначенных вам заказов\n"
            "/order_<id> - Просмотр конкретного заказа по его ID\n\n"
            "Как техник, вы можете просматривать назначенные вам заказы, "
            "обновлять их статус и добавлять информацию о стоимости и выполненных работах."
        )
    
    bot.send_message(
        user_id,
        help_text,
        reply_markup=get_back_to_main_menu_keyboard(),
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['new_order'])
def handle_new_order_command(message):
    """
    Обработчик команды /new_order (только для диспетчеров)
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, является ли пользователь диспетчером
    if not is_dispatcher(user_id):
        bot.send_message(
            user_id,
            "⚠️ У вас нет прав для создания заказов. Эта функция доступна только диспетчерам.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Начинаем процесс создания заказа
    bot.send_message(
        user_id,
        "📝 *Создание нового заказа*\n\n"
        "Введите номер телефона клиента:",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_phone")


@bot.message_handler(commands=['my_orders'])
def handle_my_orders_command(message):
    """
    Обработчик команды /my_orders (для диспетчеров)
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, является ли пользователь диспетчером
    if not is_dispatcher(user_id):
        bot.send_message(
            user_id,
            "⚠️ У вас нет прав для просмотра заказов. Эта функция доступна только диспетчерам.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем заказы пользователя
    orders = get_orders_by_user(user_id)
    
    # Форматируем и отправляем список заказов
    message_text, keyboard = format_orders_list(orders)
    
    bot.send_message(
        user_id,
        message_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['my_assigned_orders'])
def handle_my_assigned_orders_command(message):
    """
    Обработчик команды /my_assigned_orders (для техников)
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, является ли пользователь техником
    if not is_technician(user_id):
        bot.send_message(
            user_id,
            "⚠️ У вас нет прав для просмотра назначенных заказов. "
            "Эта функция доступна только техникам.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем назначенные технику заказы
    orders = get_assigned_orders(user_id)
    
    # Форматируем и отправляем список заказов
    message_text, keyboard = format_orders_list(orders)
    
    bot.send_message(
        user_id,
        message_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['all_orders'])
def handle_all_orders_command(message):
    """
    Обработчик команды /all_orders (только для администраторов)
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.send_message(
            user_id,
            "⚠️ У вас нет прав для просмотра всех заказов. "
            "Эта функция доступна только администраторам.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем все заказы
    orders = get_all_orders()
    
    # Форматируем и отправляем список заказов
    message_text, keyboard = format_orders_list(orders)
    
    bot.send_message(
        user_id,
        message_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['manage_users'])
def handle_manage_users_command(message):
    """
    Обработчик команды /manage_users (только для администраторов)
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.send_message(
            user_id,
            "⚠️ У вас нет прав для управления пользователями. "
            "Эта функция доступна только администраторам.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    bot.send_message(
        user_id,
        "👥 *Управление пользователями*\n\n"
        "Выберите действие:",
        reply_markup=get_user_management_keyboard(),
        parse_mode='Markdown'
    )


@bot.message_handler(regexp=r'^/order_(\d+)$')
def handle_order_command(message):
    """
    Обработчик команды /order_<id> для быстрого перехода к заказу
    """
    user_id = message.from_user.id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id):
        bot.send_message(
            user_id,
            "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
            parse_mode='Markdown'
        )
        return
    
    # Извлекаем ID заказа из команды
    order_id = int(message.text.split('_')[1])
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.send_message(
            user_id,
            f"⚠️ Заказ #{order_id} не найден.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
        keyboard = get_order_management_keyboard(order_id)
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
        keyboard = get_order_management_keyboard(order_id)
    elif is_technician(user_id):
        # Техники имеют доступ только к назначенным им заказам
        technicians = get_order_technicians(order_id)
        if any(tech['technician_id'] == user_id for tech in technicians):
            has_access = True
            keyboard = get_technician_order_keyboard(order_id)
    
    if not has_access:
        bot.send_message(
            user_id,
            f"⚠️ У вас нет доступа к заказу #{order_id}.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Создаем объект заказа
    order_obj = Order.from_dict(order)
    
    # Отправляем информацию о заказе
    bot.send_message(
        user_id,
        order_obj.format_for_display(),
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """
    Обработчик всех callback-запросов от inline-кнопок
    """
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    # Проверяем, подтвержден ли пользователь
    if not is_user_approved(user_id) and call.data != "main_menu":
        bot.answer_callback_query(call.id, "⚠️ Ваша учетная запись ожидает подтверждения администратором.")
        return
    
    # Обрабатываем различные типы callback-запросов
    if call.data == "main_menu":
        handle_main_menu_callback(user_id, message_id)
    elif call.data == "help":
        handle_help_callback(user_id, message_id)
    elif call.data == "new_order":
        handle_new_order_callback(user_id, message_id)
    elif call.data == "my_orders":
        handle_my_orders_callback(user_id, message_id)
    elif call.data == "my_assigned_orders":
        handle_my_assigned_orders_callback(user_id, message_id)
    elif call.data == "all_orders":
        handle_all_orders_callback(user_id, message_id)
    elif call.data == "manage_users":
        handle_manage_users_callback(user_id, message_id)
    elif call.data == "list_users":
        handle_list_users_callback(user_id, message_id)
    elif call.data == "approval_requests":
        handle_approval_requests_callback(user_id, message_id)
    elif call.data.startswith("approve_"):
        user_to_approve = int(call.data.split("_")[1])
        handle_approve_user_callback(user_id, message_id, user_to_approve)
    elif call.data.startswith("reject_"):
        user_to_reject = int(call.data.split("_")[1])
        handle_reject_user_callback(user_id, message_id, user_to_reject)
    elif call.data == "add_admin":
        handle_add_admin_callback(user_id, message_id)
    elif call.data == "add_dispatcher":
        handle_add_dispatcher_callback(user_id, message_id)
    elif call.data == "add_technician":
        handle_add_technician_callback(user_id, message_id)
    elif call.data.startswith("order_"):
        order_id = int(call.data.split("_")[1])
        handle_order_detail_callback(user_id, message_id, order_id)
    elif call.data.startswith("change_status_"):
        order_id = int(call.data.split("_")[2])
        handle_change_status_callback(user_id, message_id, order_id)
    elif call.data.startswith("status_"):
        parts = call.data.split("_")
        order_id = int(parts[1])
        status = parts[2]
        handle_update_status_callback(user_id, message_id, order_id, status)
    elif call.data.startswith("assign_technician_"):
        order_id = int(call.data.split("_")[2])
        handle_assign_technician_callback(user_id, message_id, order_id)
    elif call.data.startswith("assign_"):
        parts = call.data.split("_")
        order_id = int(parts[1])
        technician_id = int(parts[2])
        handle_assign_order_callback(user_id, message_id, order_id, technician_id)
    elif call.data.startswith("add_cost_"):
        order_id = int(call.data.split("_")[2])
        handle_add_cost_callback(user_id, message_id, order_id)
    elif call.data.startswith("add_description_"):
        order_id = int(call.data.split("_")[2])
        handle_add_description_callback(user_id, message_id, order_id)
    
    # Отмечаем callback-запрос как обработанный
    bot.answer_callback_query(call.id)


def handle_main_menu_callback(user_id, message_id):
    """
    Обработчик callback-запроса main_menu
    """
    bot.edit_message_text(
        "👋 Добро пожаловать в бот сервиса ремонта компьютеров!\n\n"
        "Выберите действие в меню ниже:",
        user_id,
        message_id,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )
    clear_user_state(user_id)


def handle_help_callback(user_id, message_id):
    """
    Обработчик callback-запроса help
    """
    # Получаем роль пользователя для отображения соответствующей справки
    role = get_user_role(user_id)
    
    # Базовая справка для всех пользователей
    help_text = (
        "🔍 *Справка по использованию бота*\n\n"
        "Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
    )
    
    # Добавляем специфичную для роли справку
    if role == 'admin':
        help_text += (
            "*Команды для администратора:*\n"
            "/all_orders - Просмотр всех заказов\n"
            "/manage_users - Управление пользователями\n"
            "/order_<id> - Просмотр конкретного заказа по его ID\n\n"
            "Как администратор, вы можете подтверждать новых пользователей, "
            "управлять заказами и назначать техников на заказы."
        )
    elif role == 'dispatcher':
        help_text += (
            "*Команды для диспетчера:*\n"
            "/new_order - Создать новый заказ\n"
            "/my_orders - Просмотр ваших заказов\n"
            "/order_<id> - Просмотр конкретного заказа по его ID\n\n"
            "Как диспетчер, вы можете создавать новые заказы и отслеживать их выполнение."
        )
    elif role == 'technician':
        help_text += (
            "*Команды для техника:*\n"
            "/my_assigned_orders - Просмотр назначенных вам заказов\n"
            "/order_<id> - Просмотр конкретного заказа по его ID\n\n"
            "Как техник, вы можете просматривать назначенные вам заказы, "
            "обновлять их статус и добавлять информацию о стоимости и выполненных работах."
        )
    
    bot.edit_message_text(
        help_text,
        user_id,
        message_id,
        reply_markup=get_back_to_main_menu_keyboard(),
        parse_mode='Markdown'
    )


def handle_new_order_callback(user_id, message_id):
    """
    Обработчик callback-запроса new_order
    """
    # Проверяем, является ли пользователь диспетчером
    if not is_dispatcher(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для создания заказов. Эта функция доступна только диспетчерам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    bot.edit_message_text(
        "📝 *Создание нового заказа*\n\n"
        "Введите номер телефона клиента:",
        user_id,
        message_id,
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_phone")


def handle_my_orders_callback(user_id, message_id):
    """
    Обработчик callback-запроса my_orders
    """
    # Проверяем, является ли пользователь диспетчером
    if not is_dispatcher(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для просмотра заказов. Эта функция доступна только диспетчерам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем заказы пользователя
    orders = get_orders_by_user(user_id)
    
    # Форматируем и отправляем список заказов
    message_text, keyboard = format_orders_list(orders)
    
    bot.edit_message_text(
        message_text,
        user_id,
        message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


def handle_my_assigned_orders_callback(user_id, message_id):
    """
    Обработчик callback-запроса my_assigned_orders
    """
    # Проверяем, является ли пользователь техником
    if not is_technician(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для просмотра назначенных заказов. "
            "Эта функция доступна только техникам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем назначенные технику заказы
    orders = get_assigned_orders(user_id)
    
    # Форматируем и отправляем список заказов
    message_text, keyboard = format_orders_list(orders)
    
    bot.edit_message_text(
        message_text,
        user_id,
        message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


def handle_all_orders_callback(user_id, message_id):
    """
    Обработчик callback-запроса all_orders
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для просмотра всех заказов. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем все заказы
    orders = get_all_orders()
    
    # Форматируем и отправляем список заказов
    message_text, keyboard = format_orders_list(orders)
    
    bot.edit_message_text(
        message_text,
        user_id,
        message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


def handle_manage_users_callback(user_id, message_id):
    """
    Обработчик callback-запроса manage_users
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для управления пользователями. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    bot.edit_message_text(
        "👥 *Управление пользователями*\n\n"
        "Выберите действие:",
        user_id,
        message_id,
        reply_markup=get_user_management_keyboard(),
        parse_mode='Markdown'
    )


def handle_list_users_callback(user_id, message_id):
    """
    Обработчик callback-запроса list_users
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для просмотра списка пользователей. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем всех пользователей
    users = get_all_users()
    
    if not users:
        bot.edit_message_text(
            "👥 *Список пользователей пуст*",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Формируем сообщение
    message_text = "👥 *Список пользователей:*\n\n"
    
    for i, user in enumerate(users):
        name = user['first_name']
        if user['last_name']:
            name += f" {user['last_name']}"
        
        username = f"@{user['username']}" if user['username'] else "без имени пользователя"
        role = get_role_name(user['role'])
        approved = "✅ Подтвержден" if user['is_approved'] else "❌ Не подтвержден"
        
        message_text += (
            f"{i+1}. *{name}* ({username})\n"
            f"   Роль: {role}\n"
            f"   Статус: {approved}\n"
            f"   ID: `{user['user_id']}`\n\n"
        )
    
    # Если сообщение слишком длинное, разбиваем его на части
    max_length = 4096  # Максимальная длина сообщения в Telegram
    
    if len(message_text) <= max_length:
        bot.edit_message_text(
            message_text,
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    else:
        # Отправляем первую часть, заменяя текущее сообщение
        bot.edit_message_text(
            message_text[:max_length],
            user_id,
            message_id,
            parse_mode='Markdown'
        )
        
        # Отправляем остальные части как новые сообщения
        remaining_text = message_text[max_length:]
        
        while remaining_text:
            part = remaining_text[:max_length]
            remaining_text = remaining_text[max_length:]
            
            # Последнее сообщение с кнопкой возврата
            if not remaining_text:
                bot.send_message(
                    user_id,
                    part,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    user_id,
                    part,
                    parse_mode='Markdown'
                )


def handle_approval_requests_callback(user_id, message_id):
    """
    Обработчик callback-запроса approval_requests
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для управления запросами на подтверждение. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем клавиатуру с запросами на подтверждение
    message_text, keyboard = get_approval_requests_keyboard()
    
    bot.edit_message_text(
        message_text,
        user_id,
        message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


def handle_approve_user_callback(user_id, message_id, user_to_approve):
    """
    Обработчик подтверждения пользователя
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для подтверждения пользователей. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Подтверждаем пользователя
    if approve_user(user_to_approve):
        # Получаем информацию о пользователе
        user_info = get_user(user_to_approve)
        if user_info:
            name = user_info['first_name']
            if user_info['last_name']:
                name += f" {user_info['last_name']}"
            
            # Уведомляем администратора о успешном подтверждении
            bot.edit_message_text(
                f"✅ Пользователь *{name}* успешно подтвержден.",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
            # Уведомляем пользователя о подтверждении
            try:
                bot.send_message(
                    user_to_approve,
                    "✅ Ваша учетная запись подтверждена администратором. "
                    "Теперь вы можете использовать все доступные функции бота.",
                    reply_markup=get_main_menu_keyboard(user_to_approve),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {user_to_approve}: {e}")
        else:
            bot.edit_message_text(
                "⚠️ Не удалось получить информацию о пользователе.",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode='Markdown'
            )
    else:
        bot.edit_message_text(
            "⚠️ Не удалось подтвердить пользователя. Попробуйте позже.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )


def handle_reject_user_callback(user_id, message_id, user_to_reject):
    """
    Обработчик отклонения пользователя
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для отклонения пользователей. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем информацию о пользователе перед отклонением
    user_info = get_user(user_to_reject)
    if user_info:
        name = user_info['first_name']
        if user_info['last_name']:
            name += f" {user_info['last_name']}"
        
        # Отклоняем пользователя
        if reject_user(user_to_reject):
            # Уведомляем администратора о успешном отклонении
            bot.edit_message_text(
                f"❌ Пользователь *{name}* отклонен.",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
            # Уведомляем пользователя об отклонении
            try:
                bot.send_message(
                    user_to_reject,
                    "❌ Ваша заявка на использование бота отклонена администратором.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {user_to_reject}: {e}")
        else:
            bot.edit_message_text(
                "⚠️ Не удалось отклонить пользователя. Попробуйте позже.",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode='Markdown'
            )
    else:
        bot.edit_message_text(
            "⚠️ Не удалось получить информацию о пользователе.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )


def handle_add_admin_callback(user_id, message_id):
    """
    Обработчик callback-запроса add_admin
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для добавления администраторов. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    bot.edit_message_text(
        "👑 *Добавление нового администратора*\n\n"
        "Введите ID пользователя, которого хотите сделать администратором:\n"
        "(ID можно узнать, если пользователь отправит боту любое сообщение, "
        "и вы посмотрите список запросов на подтверждение)",
        user_id,
        message_id,
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_admin_id")


def handle_add_dispatcher_callback(user_id, message_id):
    """
    Обработчик callback-запроса add_dispatcher
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для добавления диспетчеров. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    bot.edit_message_text(
        "📞 *Добавление нового диспетчера*\n\n"
        "Введите ID пользователя, которого хотите сделать диспетчером:\n"
        "(ID можно узнать, если пользователь отправит боту любое сообщение, "
        "и вы посмотрите список запросов на подтверждение)",
        user_id,
        message_id,
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_dispatcher_id")


def handle_add_technician_callback(user_id, message_id):
    """
    Обработчик callback-запроса add_technician
    """
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.edit_message_text(
            "⚠️ У вас нет прав для добавления техников. "
            "Эта функция доступна только администраторам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    bot.edit_message_text(
        "🔧 *Добавление нового техника*\n\n"
        "Введите ID пользователя, которого хотите сделать техником:\n"
        "(ID можно узнать, если пользователь отправит боту любое сообщение, "
        "и вы посмотрите список запросов на подтверждение)",
        user_id,
        message_id,
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_technician_id")


def handle_order_detail_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса order_{order_id}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
        keyboard = get_order_management_keyboard(order_id)
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
        keyboard = get_order_management_keyboard(order_id)
    elif is_technician(user_id):
        # Техники имеют доступ только к назначенным им заказам
        technicians = get_order_technicians(order_id)
        if any(tech['technician_id'] == user_id for tech in technicians):
            has_access = True
            keyboard = get_technician_order_keyboard(order_id)
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет доступа к заказу #{order_id}.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Создаем объект заказа
    order_obj = Order.from_dict(order)
    
    # Отправляем информацию о заказе
    bot.edit_message_text(
        order_obj.format_for_display(),
        user_id,
        message_id,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


def handle_change_status_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса change_status_{order_id}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
    elif is_technician(user_id):
        # Техники имеют доступ только к назначенным им заказам
        technicians = get_order_technicians(order_id)
        if any(tech['technician_id'] == user_id for tech in technicians):
            has_access = True
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет доступа к заказу #{order_id}.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Отправляем клавиатуру для изменения статуса
    bot.edit_message_text(
        f"🔄 *Изменение статуса заказа #{order_id}*\n\n"
        f"Текущий статус: {get_status_name(order['status'])}\n\n"
        f"Выберите новый статус:",
        user_id,
        message_id,
        reply_markup=get_order_status_keyboard(order_id),
        parse_mode='Markdown'
    )


def handle_update_status_callback(user_id, message_id, order_id, status):
    """
    Обработчик callback-запроса status_{order_id}_{status}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
        keyboard = get_order_management_keyboard(order_id)
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
        keyboard = get_order_management_keyboard(order_id)
    elif is_technician(user_id):
        # Техники имеют доступ только к назначенным им заказам
        technicians = get_order_technicians(order_id)
        if any(tech['technician_id'] == user_id for tech in technicians):
            has_access = True
            keyboard = get_technician_order_keyboard(order_id)
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет доступа к заказу #{order_id}.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Обновляем статус заказа
    if update_order(order_id, status=status):
        # Получаем обновленную информацию о заказе
        updated_order = get_order(order_id)
        if updated_order:
            order_obj = Order.from_dict(updated_order)
            
            bot.edit_message_text(
                f"✅ Статус заказа #{order_id} изменен на "
                f"*{get_status_name(status)}*.\n\n"
                f"{order_obj.format_for_display()}",
                user_id,
                message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # Если техник завершил заказ, отправляем уведомление диспетчеру
            if status == 'completed' and is_technician(user_id):
                try:
                    dispatcher_id = updated_order['dispatcher_id']
                    if dispatcher_id:
                        bot.send_message(
                            dispatcher_id,
                            f"✅ Заказ #{order_id} завершен техником.\n\n"
                            f"Клиент: {updated_order['client_name']}\n"
                            f"Телефон: {updated_order['client_phone']}\n\n"
                            f"Для просмотра деталей: /order_{order_id}",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления диспетчеру {dispatcher_id}: {e}")
        else:
            bot.edit_message_text(
                f"✅ Статус заказа #{order_id} изменен на *{get_status_name(status)}*.",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode='Markdown'
            )
    else:
        bot.edit_message_text(
            f"⚠️ Не удалось изменить статус заказа #{order_id}. Попробуйте позже.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )


def handle_assign_technician_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса assign_technician_{order_id}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу (только администраторы и диспетчеры)
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет прав для назначения техников. "
            f"Эта функция доступна только администраторам и диспетчерам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем список техников, уже назначенных на заказ
    assigned_technicians = get_order_technicians(order_id)
    assigned_names = []
    
    for tech in assigned_technicians:
        name = tech['first_name']
        if tech['last_name']:
            name += f" {tech['last_name']}"
        assigned_names.append(name)
    
    # Формируем сообщение
    message_text = f"👨‍🔧 *Назначение техника на заказ #{order_id}*\n\n"
    
    if assigned_names:
        message_text += "Уже назначены:\n" + "\n".join([f"- {name}" for name in assigned_names]) + "\n\n"
    
    message_text += "Выберите техника для назначения:"
    
    bot.edit_message_text(
        message_text,
        user_id,
        message_id,
        reply_markup=get_technician_list_keyboard(order_id),
        parse_mode='Markdown'
    )


def handle_assign_order_callback(user_id, message_id, order_id, technician_id):
    """
    Обработчик callback-запроса assign_{order_id}_{technician_id}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу (только администраторы и диспетчеры)
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет прав для назначения техников. "
            f"Эта функция доступна только администраторам и диспетчерам.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Получаем информацию о технике
    technician = get_user(technician_id)
    
    if not technician:
        bot.edit_message_text(
            f"⚠️ Техник не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Назначаем техника на заказ
    if assign_order(order_id, technician_id, user_id):
        tech_name = technician['first_name']
        if technician['last_name']:
            tech_name += f" {technician['last_name']}"
        
        bot.edit_message_text(
            f"✅ Техник *{tech_name}* успешно назначен на заказ #{order_id}.",
            user_id,
            message_id,
            reply_markup=get_order_management_keyboard(order_id),
            parse_mode='Markdown'
        )
        
        # Отправляем уведомление технику
        try:
            bot.send_message(
                technician_id,
                f"📋 *Вам назначен новый заказ #{order_id}*\n\n"
                f"Клиент: {order['client_name']}\n"
                f"Телефон: {order['client_phone']}\n"
                f"Адрес: {order['client_address']}\n"
                f"Проблема: {order['problem_description']}\n\n"
                f"Для просмотра деталей: /order_{order_id}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления технику {technician_id}: {e}")
    else:
        bot.edit_message_text(
            f"⚠️ Не удалось назначить техника на заказ #{order_id}. Попробуйте позже.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )


def handle_add_cost_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса add_cost_{order_id}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
    elif is_technician(user_id):
        # Техники имеют доступ только к назначенным им заказам
        technicians = get_order_technicians(order_id)
        if any(tech['technician_id'] == user_id for tech in technicians):
            has_access = True
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет доступа к заказу #{order_id}.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем текущий статус заказа
    if order['status'] not in ['in_progress', 'completed']:
        bot.edit_message_text(
            f"⚠️ Добавление стоимости доступно только для заказов "
            f"в статусе 'В работе' или 'Завершен'.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Отправляем запрос на ввод стоимости
    current_cost = order['service_cost'] if order['service_cost'] else 'не указана'
    
    bot.edit_message_text(
        f"💰 *Добавление стоимости для заказа #{order_id}*\n\n"
        f"Текущая стоимость: {current_cost}\n\n"
        f"Введите новую стоимость (только число, например 1500):",
        user_id,
        message_id,
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_cost", order_id)


def handle_add_description_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса add_description_{order_id}
    """
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            f"⚠️ Заказ #{order_id} не найден.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем права доступа к заказу
    has_access = False
    
    if is_admin(user_id):
        # Администраторы имеют доступ ко всем заказам
        has_access = True
    elif is_dispatcher(user_id) and order['dispatcher_id'] == user_id:
        # Диспетчеры имеют доступ только к своим заказам
        has_access = True
    elif is_technician(user_id):
        # Техники имеют доступ только к назначенным им заказам
        technicians = get_order_technicians(order_id)
        if any(tech['technician_id'] == user_id for tech in technicians):
            has_access = True
    
    if not has_access:
        bot.edit_message_text(
            f"⚠️ У вас нет доступа к заказу #{order_id}.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем текущий статус заказа
    if order['status'] not in ['in_progress', 'completed']:
        bot.edit_message_text(
            f"⚠️ Добавление описания работ доступно только для заказов "
            f"в статусе 'В работе' или 'Завершен'.",
            user_id,
            message_id,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Отправляем запрос на ввод описания работ
    current_description = order['service_description'] if order['service_description'] else 'не указано'
    
    bot.edit_message_text(
        f"📝 *Добавление описания работ для заказа #{order_id}*\n\n"
        f"Текущее описание: {current_description}\n\n"
        f"Введите новое описание выполненных работ:",
        user_id,
        message_id,
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_description", order_id)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Обработчик всех текстовых сообщений
    """
    user_id = message.from_user.id
    text = message.text
    
    # Получаем текущее состояние пользователя
    state = get_user_state(user_id)
    
    # Если пользователь новый, сохраняем его информацию
    user = get_user(user_id)
    if not user:
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        save_user(user_id, first_name, last_name, username)
        
        # Отправляем сообщение о том, что аккаунт ожидает подтверждения
        bot.send_message(
            user_id,
            "👋 Добро пожаловать в бот сервиса ремонта компьютеров!\n\n"
            "Ваша учетная запись ожидает подтверждения администратором. "
            "Вы получите уведомление, когда ваша учетная запись будет активирована.",
            parse_mode='Markdown'
        )
        
        # Уведомляем всех администраторов о новом пользователе
        admins = [u for u in get_all_users() if u['role'] == 'admin']
        for admin in admins:
            try:
                bot.send_message(
                    admin['user_id'],
                    f"👤 *Новый пользователь запрашивает доступ*\n\n"
                    f"Имя: {first_name} {last_name or ''}\n"
                    f"Username: @{username or 'отсутствует'}\n"
                    f"ID: `{user_id}`\n\n"
                    f"Для управления запросами используйте команду /manage_users",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору {admin['user_id']}: {e}")
        
        return
    
    # Проверяем, подтвержден ли пользователь (кроме состояния ввода ID для назначения роли)
    if not state or not state.startswith("waiting_for_") or state == "waiting_for_phone":
        if not is_user_approved(user_id):
            bot.send_message(
                user_id,
                "⚠️ Ваша учетная запись ожидает подтверждения администратором.",
                parse_mode='Markdown'
            )
            return
    
    # Обрабатываем сообщение в зависимости от текущего состояния пользователя
    if state == "waiting_for_phone":
        handle_phone_input(user_id, text)
    elif state == "waiting_for_name":
        handle_name_input(user_id, text)
    elif state == "waiting_for_address":
        handle_address_input(user_id, text)
    elif state == "waiting_for_problem":
        handle_problem_input(user_id, text)
    elif state == "waiting_for_admin_id":
        handle_user_id_input(user_id, text, "admin")
    elif state == "waiting_for_dispatcher_id":
        handle_user_id_input(user_id, text, "dispatcher")
    elif state == "waiting_for_technician_id":
        handle_user_id_input(user_id, text, "technician")
    elif state == "waiting_for_cost":
        handle_cost_input(user_id, text)
    elif state == "waiting_for_description":
        handle_description_input(user_id, text)
    else:
        # Если у пользователя нет активного состояния, отправляем приветственное сообщение
        bot.send_message(
            user_id,
            "👋 Добро пожаловать в бот сервиса ремонта компьютеров!\n\n"
            "Выберите действие в меню ниже:",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )


def handle_phone_input(user_id, text):
    """
    Обработка ввода номера телефона
    """
    # Проверяем формат номера телефона
    if not validate_phone(text):
        bot.send_message(
            user_id,
            "⚠️ Неверный формат номера телефона. Пожалуйста, введите номер в формате "
            "+7XXXXXXXXXX или 8XXXXXXXXXX.",
            parse_mode='Markdown'
        )
        return
    
    # Сохраняем номер телефона и переходим к следующему шагу
    set_user_state(user_id, "waiting_for_name")
    
    # Временно сохраняем данные в user_data
    user_id_str = str(user_id)
    if not hasattr(bot, 'user_data'):
        bot.user_data = {}
    if user_id_str not in bot.user_data:
        bot.user_data[user_id_str] = {}
    
    bot.user_data[user_id_str]['phone'] = text
    
    bot.send_message(
        user_id,
        "📝 Введите имя клиента:",
        parse_mode='Markdown'
    )


def handle_name_input(user_id, text):
    """
    Обработка ввода имени клиента
    """
    # Сохраняем имя клиента и переходим к следующему шагу
    set_user_state(user_id, "waiting_for_address")
    
    # Временно сохраняем данные
    user_id_str = str(user_id)
    if not hasattr(bot, 'user_data'):
        bot.user_data = {}
    if user_id_str not in bot.user_data:
        bot.user_data[user_id_str] = {}
    
    bot.user_data[user_id_str]['name'] = text
    
    bot.send_message(
        user_id,
        "📝 Введите адрес клиента:",
        parse_mode='Markdown'
    )


def handle_address_input(user_id, text):
    """
    Обработка ввода адреса клиента
    """
    # Сохраняем адрес клиента и переходим к следующему шагу
    set_user_state(user_id, "waiting_for_problem")
    
    # Временно сохраняем данные
    user_id_str = str(user_id)
    if not hasattr(bot, 'user_data'):
        bot.user_data = {}
    if user_id_str not in bot.user_data:
        bot.user_data[user_id_str] = {}
    
    bot.user_data[user_id_str]['address'] = text
    
    bot.send_message(
        user_id,
        "📝 Введите описание проблемы:",
        parse_mode='Markdown'
    )


def handle_problem_input(user_id, text):
    """
    Обработка ввода описания проблемы
    """
    user_id_str = str(user_id)
    if not hasattr(bot, 'user_data'):
        bot.user_data = {}
    if user_id_str not in bot.user_data:
        bot.user_data[user_id_str] = {}
        bot.send_message(
            user_id,
            "⚠️ Ошибка: данные заказа не найдены. Пожалуйста, начните заново.",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        clear_user_state(user_id)
        return
    
    # Получаем данные заказа
    phone = bot.user_data[user_id_str].get('phone')
    name = bot.user_data[user_id_str].get('name')
    address = bot.user_data[user_id_str].get('address')
    problem = text
    
    # Очищаем временные данные
    bot.user_data[user_id_str] = {}
    
    # Сохраняем заказ в базе данных
    order_id = save_order(user_id, phone, name, address, problem)
    
    if order_id:
        # Формируем сообщение о созданном заказе
        order = get_order(order_id)
        if order:
            order_obj = Order.from_dict(order)
            
            bot.send_message(
                user_id,
                f"✅ Заказ #{order_id} успешно создан!\n\n"
                f"{order_obj.format_for_display()}",
                reply_markup=get_order_management_keyboard(order_id),
                parse_mode='Markdown'
            )
            
            # Отправляем уведомление администраторам
            send_order_notification_to_admins(bot, order_id)
        else:
            bot.send_message(
                user_id,
                f"✅ Заказ #{order_id} успешно создан!",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode='Markdown'
            )
    else:
        bot.send_message(
            user_id,
            "⚠️ Ошибка при создании заказа. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
    
    # Очищаем состояние пользователя
    clear_user_state(user_id)


def handle_user_id_input(user_id, text, role):
    """
    Обработка ввода ID пользователя для назначения роли
    """
    try:
        # Проверяем, является ли введенный текст числом
        target_user_id = int(text.strip())
        
        # Проверяем, существует ли пользователь
        target_user = get_user(target_user_id)
        
        if not target_user:
            bot.send_message(
                user_id,
                f"⚠️ Пользователь с ID {target_user_id} не найден. "
                f"Пожалуйста, проверьте ID и попробуйте снова.",
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            return
        
        # Обновляем роль пользователя и подтверждаем его
        if update_user_role(target_user_id, role) and approve_user(target_user_id):
            name = target_user['first_name']
            if target_user['last_name']:
                name += f" {target_user['last_name']}"
            
            role_name = get_role_name(role)
            
            bot.send_message(
                user_id,
                f"✅ Пользователь *{name}* успешно добавлен как {role_name}.",
                reply_markup=get_user_management_keyboard(),
                parse_mode='Markdown'
            )
            
            # Уведомляем пользователя о назначении роли
            try:
                bot.send_message(
                    target_user_id,
                    f"✅ Администратор добавил вас в систему как: {role_name}.\n\n"
                    f"Теперь вы можете использовать все доступные функции бота.",
                    reply_markup=get_main_menu_keyboard(target_user_id),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
        else:
            bot.send_message(
                user_id,
                f"⚠️ Ошибка при добавлении пользователя. Пожалуйста, попробуйте позже.",
                reply_markup=get_user_management_keyboard(),
                parse_mode='Markdown'
            )
    except ValueError:
        bot.send_message(
            user_id,
            "⚠️ Неверный формат ID пользователя. ID должен быть числом.",
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    # Очищаем состояние пользователя
    clear_user_state(user_id)


def handle_cost_input(user_id, text):
    """
    Обработка ввода стоимости услуг
    """
    # Получаем ID текущего заказа
    order_id = get_current_order_id(user_id)
    
    if not order_id:
        bot.send_message(
            user_id,
            "⚠️ Ошибка: заказ не найден. Пожалуйста, начните заново.",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        clear_user_state(user_id)
        return
    
    try:
        # Преобразуем введенный текст в число
        cost = float(text.strip().replace(',', '.'))
        
        # Обновляем стоимость заказа
        if update_order(order_id, service_cost=cost):
            # Получаем обновленную информацию о заказе
            order = get_order(order_id)
            if order:
                # Определяем какую клавиатуру показать
                if is_admin(user_id) or (is_dispatcher(user_id) and order['dispatcher_id'] == user_id):
                    keyboard = get_order_management_keyboard(order_id)
                else:
                    keyboard = get_technician_order_keyboard(order_id)
                
                # Создаем объект заказа
                order_obj = Order.from_dict(order)
                
                bot.send_message(
                    user_id,
                    f"✅ Стоимость заказа #{order_id} успешно обновлена!\n\n"
                    f"{order_obj.format_for_display()}",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                # Если обновление делает техник, отправляем уведомление диспетчеру
                if is_technician(user_id) and order['dispatcher_id']:
                    try:
                        bot.send_message(
                            order['dispatcher_id'],
                            f"💰 Техник добавил стоимость к заказу #{order_id}:\n\n"
                            f"Стоимость: {cost} руб.\n"
                            f"Клиент: {order['client_name']}\n"
                            f"Телефон: {order['client_phone']}\n\n"
                            f"Для просмотра деталей: /order_{order_id}",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления диспетчеру {order['dispatcher_id']}: {e}")
            else:
                bot.send_message(
                    user_id,
                    f"✅ Стоимость заказа #{order_id} успешно обновлена!",
                    reply_markup=get_main_menu_keyboard(user_id),
                    parse_mode='Markdown'
                )
        else:
            bot.send_message(
                user_id,
                f"⚠️ Ошибка при обновлении стоимости заказа. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode='Markdown'
            )
    except ValueError:
        bot.send_message(
            user_id,
            "⚠️ Неверный формат стоимости. Введите число (например, 1500).",
            parse_mode='Markdown'
        )
        return
    
    # Очищаем состояние пользователя
    clear_user_state(user_id)


def handle_description_input(user_id, text):
    """
    Обработка ввода описания выполненных работ
    """
    # Получаем ID текущего заказа
    order_id = get_current_order_id(user_id)
    
    if not order_id:
        bot.send_message(
            user_id,
            "⚠️ Ошибка: заказ не найден. Пожалуйста, начните заново.",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        clear_user_state(user_id)
        return
    
    # Обновляем описание работ
    if update_order(order_id, service_description=text):
        # Получаем обновленную информацию о заказе
        order = get_order(order_id)
        if order:
            # Определяем какую клавиатуру показать
            if is_admin(user_id) or (is_dispatcher(user_id) and order['dispatcher_id'] == user_id):
                keyboard = get_order_management_keyboard(order_id)
            else:
                keyboard = get_technician_order_keyboard(order_id)
            
            # Создаем объект заказа
            order_obj = Order.from_dict(order)
            
            bot.send_message(
                user_id,
                f"✅ Описание работ для заказа #{order_id} успешно обновлено!\n\n"
                f"{order_obj.format_for_display()}",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # Если обновление делает техник, отправляем уведомление диспетчеру
            if is_technician(user_id) and order['dispatcher_id']:
                try:
                    description_short = text if len(text) <= 100 else text[:97] + "..."
                    
                    bot.send_message(
                        order['dispatcher_id'],
                        f"📝 Техник добавил описание работ к заказу #{order_id}:\n\n"
                        f"Описание: {description_short}\n"
                        f"Клиент: {order['client_name']}\n"
                        f"Телефон: {order['client_phone']}\n\n"
                        f"Для просмотра деталей: /order_{order_id}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления диспетчеру {order['dispatcher_id']}: {e}")
        else:
            bot.send_message(
                user_id,
                f"✅ Описание работ для заказа #{order_id} успешно обновлено!",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode='Markdown'
            )
    else:
        bot.send_message(
            user_id,
            f"⚠️ Ошибка при обновлении описания работ. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
    
    # Очищаем состояние пользователя
    clear_user_state(user_id)