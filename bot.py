"""
Telegram бот для управления заказами сервиса ремонта компьютеров
"""

import os
import logging
import re
from typing import Optional, Dict, List

import telebot
from telebot.types import Message, CallbackQuery

from config import ROLES, ORDER_STATUSES
from database import (
    save_user, get_user, get_all_users, get_user_role, is_user_approved,
    get_unapproved_users, approve_user, reject_user, update_user_role,
    save_order, update_order, get_order, get_orders_by_user, get_all_orders,
    get_assigned_orders, assign_order, get_technicians, get_order_technicians,
    set_user_state, get_user_state, get_current_order_id, clear_user_state
)
from utils import (
    get_main_menu_keyboard, get_order_status_keyboard, get_order_management_keyboard,
    get_technician_order_keyboard, get_back_to_main_menu_keyboard, get_approval_requests_keyboard,
    get_user_management_keyboard, is_admin, is_dispatcher, is_technician,
    send_order_notification_to_admins, validate_phone, format_orders_list, get_technician_list_keyboard
)

# Конфигурация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем бота
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения временных данных пользователей
user_data = {}

# Обработчики состояний пользователей
def set_user_state(user_id: int, state: str, order_id: Optional[int] = None) -> None:
    """
    Устанавливает состояние пользователя
    """
    from database import set_user_state as db_set_user_state
    db_set_user_state(user_id, state, order_id)

def clear_user_state(user_id: int) -> None:
    """
    Очищает состояние пользователя
    """
    from database import clear_user_state as db_clear_user_state
    db_clear_user_state(user_id)

def get_user_state(user_id: int) -> Optional[str]:
    """
    Возвращает текущее состояние пользователя
    """
    from database import get_user_state as db_get_user_state
    return db_get_user_state(user_id)

def get_current_order_id(user_id: int) -> Optional[int]:
    """
    Возвращает ID текущего заказа пользователя
    """
    from database import get_current_order_id as db_get_current_order_id
    return db_get_current_order_id(user_id)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    """
    Обработчик команды /start
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    
    # Сохраняем информацию о пользователе в БД
    save_user(user_id, first_name, last_name, username)
    
    # Получаем актуальную информацию о пользователе
    user = get_user(user_id)
    
    if not user:
        bot.reply_to(message, "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        return
    
    greeting = f"Здравствуйте, {user.get_full_name()}!"
    
    if user.is_approved:
        if user.is_admin():
            bot.send_message(
                user_id,
                f"{greeting}\nВы вошли как *Администратор*.\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
        elif user.is_dispatcher():
            bot.send_message(
                user_id,
                f"{greeting}\nВы вошли как *Диспетчер*.\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
        elif user.is_technician():
            bot.send_message(
                user_id,
                f"{greeting}\nВы вошли как *Техник*.\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
    else:
        # Если пользователь не подтвержден
        bot.send_message(
            user_id,
            f"{greeting}\n\nВаша учетная запись находится на проверке у администратора. "
            "Вам будет отправлено уведомление после подтверждения учетной записи."
        )
        
        # Отправляем уведомление администраторам о новом пользователе
        admins = [user for user in get_all_users() if user.is_admin()]
        
        if admins:
            username_info = f" (@{username})" if username else ""
            notification = (
                f"🔔 *Новый пользователь в системе*\n\n"
                f"👤 {first_name} {last_name or ''}{username_info}\n"
                f"🆔 ID: {user_id}\n\n"
                f"Для подтверждения или отклонения используйте команду /manage_users"
            )
            
            for admin in admins:
                try:
                    bot.send_message(admin.user_id, notification, parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления администратору {admin.user_id}: {e}")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def handle_help_command(message):
    """
    Обработчик команды /help
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Формируем текст справки в зависимости от роли пользователя
    help_text = "🔍 *Справка по использованию бота*\n\n"
    
    # Общие команды для всех пользователей
    help_text += "*Общие команды:*\n"
    help_text += "/start - Начать работу с ботом\n"
    help_text += "/help - Показать эту справку\n\n"
    
    # Специфичные команды в зависимости от роли
    if user.is_admin():
        help_text += "*Команды администратора:*\n"
        help_text += "/all_orders - Просмотр всех заказов\n"
        help_text += "/manage_users - Управление пользователями\n"
        help_text += "\nКак администратор, вы можете:\n"
        help_text += "• Просматривать все заказы\n"
        help_text += "• Подтверждать новых пользователей\n"
        help_text += "• Назначать мастеров на заказы\n"
        help_text += "• Изменять статусы заказов\n"
        help_text += "• Добавлять новых администраторов и диспетчеров\n"
    elif user.is_dispatcher():
        help_text += "*Команды диспетчера:*\n"
        help_text += "/new_order - Создать новый заказ\n"
        help_text += "/my_orders - Просмотр созданных вами заказов\n"
        help_text += "\nКак диспетчер, вы можете:\n"
        help_text += "• Создавать новые заказы\n"
        help_text += "• Просматривать и редактировать созданные вами заказы\n"
    elif user.is_technician():
        help_text += "*Команды мастера:*\n"
        help_text += "/my_assigned_orders - Просмотр назначенных вам заказов\n"
        help_text += "\nКак техник, вы можете:\n"
        help_text += "• Просматривать назначенные вам заказы\n"
        help_text += "• Обновлять статус заказов\n"
        help_text += "• Добавлять стоимость выполненных работ\n"
        help_text += "• Добавлять описание выполненных работ\n"
    
    help_text += "\n*Работа с заказами:*\n"
    help_text += "• Создание заказа: указываются данные клиента и описание проблемы\n"
    help_text += "• Статусы заказов: новый → назначен → в работе → завершен\n"
    help_text += "• Для быстрого перехода к заказу используйте команду /order_<номер>\n"
    
    # Отправляем справку
    bot.send_message(user_id, help_text, parse_mode="Markdown")

# Обработчик команды /new_order (только для диспетчеров)
@bot.message_handler(commands=['new_order'])
def handle_new_order_command(message):
    """
    Обработчик команды /new_order (только для диспетчеров)
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Проверяем, является ли пользователь диспетчером или администратором
    if not (user.is_dispatcher() or user.is_admin()):
        bot.reply_to(
            message,
            "Эта команда доступна только для диспетчеров и администраторов."
        )
        return
    
    # Начинаем процесс создания заказа
    bot.send_message(
        user_id,
        "📝 *Создание нового заказа*\n\n"
        "Введите номер телефона клиента:",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_phone")

# Обработчик команды /my_orders (для диспетчеров)
@bot.message_handler(commands=['my_orders'])
def handle_my_orders_command(message):
    """
    Обработчик команды /my_orders (для диспетчеров)
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Проверяем, является ли пользователь диспетчером или администратором
    if not (user.is_dispatcher() or user.is_admin()):
        bot.reply_to(
            message,
            "Эта команда доступна только для диспетчеров и администраторов."
        )
        return
    
    # Получаем заказы пользователя
    orders = get_orders_by_user(user_id)
    
    # Форматируем список заказов и получаем клавиатуру
    message_text, keyboard = format_orders_list(orders)
    
    # Отправляем сообщение с заказами
    bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="Markdown")

# Обработчик команды /my_assigned_orders (для мастеров)
@bot.message_handler(commands=['my_assigned_orders'])
def handle_my_assigned_orders_command(message):
    """
    Обработчик команды /my_assigned_orders (для мастеров)
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Проверяем, является ли пользователь мастером
    if not user.is_technician():
        bot.reply_to(
            message,
            "Эта команда доступна только для мастеров."
        )
        return
    
    # Получаем назначенные заказы
    orders = get_assigned_orders(user_id)
    
    # Форматируем список заказов и получаем клавиатуру
    message_text, keyboard = format_orders_list(orders)
    
    # Отправляем сообщение с заказами
    bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="Markdown")

# Обработчик команды /all_orders (только для администраторов)
@bot.message_handler(commands=['all_orders'])
def handle_all_orders_command(message):
    """
    Обработчик команды /all_orders (только для администраторов)
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.reply_to(
            message,
            "Эта команда доступна только для администраторов."
        )
        return
    
    # Получаем все заказы
    orders = get_all_orders()
    
    # Форматируем список заказов и получаем клавиатуру
    message_text, keyboard = format_orders_list(orders)
    
    # Отправляем сообщение с заказами
    bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="Markdown")

# Обработчик команды /manage_users (только для администраторов)
@bot.message_handler(commands=['manage_users'])
def handle_manage_users_command(message):
    """
    Обработчик команды /manage_users (только для администраторов)
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.reply_to(
            message,
            "Эта команда доступна только для администраторов."
        )
        return
    
    # Отправляем сообщение с клавиатурой управления пользователями
    bot.send_message(
        user_id,
        "👥 *Управление пользователями*\n\n"
        "Выберите действие:",
        reply_markup=get_user_management_keyboard(),
        parse_mode="Markdown"
    )

# Обработчик команды /order_<id> для быстрого перехода к заказу
@bot.message_handler(regexp=r"^/order_(\d+)$")
def handle_order_command(message):
    """
    Обработчик команды /order_<id> для быстрого перехода к заказу
    """
    user_id = message.from_user.id
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user or not user.is_approved:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Получаем номер заказа из команды
    match = re.match(r"^/order_(\d+)$", message.text)
    if match:
        order_id = int(match.group(1))
        
        # Получаем информацию о заказе
        order = get_order(order_id)
        
        if not order:
            bot.reply_to(message, "Заказ с указанным номером не найден.")
            return
        
        # Формируем сообщение с информацией о заказе
        message_text = order.format_for_display()
        
        # Определяем тип клавиатуры в зависимости от роли пользователя
        keyboard = None
        if user.is_admin():
            keyboard = get_order_management_keyboard(order_id)
        elif user.is_dispatcher() and order.dispatcher_id == user_id:
            keyboard = get_order_management_keyboard(order_id)
        elif user.is_technician():
            # Проверяем, назначен ли заказ этому мастеру
            technicians = get_order_technicians(order_id)
            is_assigned = any(tech.technician_id == user_id for tech in technicians)
            
            if is_assigned:
                keyboard = get_technician_order_keyboard(order_id)
            else:
                keyboard = get_back_to_main_menu_keyboard()
        else:
            keyboard = get_back_to_main_menu_keyboard()
        
        # Отправляем информацию о заказе
        bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="Markdown")

# Обработчик всех callback-запросов от inline-кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """
    Обработчик всех callback-запросов от inline-кнопок
    """
    user_id = call.from_user.id
    message_id = call.message.message_id
    callback_data = call.data
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user:
        bot.answer_callback_query(
            call.id,
            "Ваша учетная запись не найдена. Пожалуйста, используйте команду /start для регистрации."
        )
        return
    
    # Проверяем подтверждение пользователя (кроме callback для главного меню)
    if not user.is_approved and callback_data != "main_menu":
        bot.answer_callback_query(
            call.id,
            "Ваша учетная запись не подтверждена администратором. Пожалуйста, дождитесь подтверждения."
        )
        return
    
    # Обрабатываем различные типы callback-запросов
    if callback_data == "main_menu":
        handle_main_menu_callback(user_id, message_id)
    elif callback_data == "help":
        handle_help_callback(user_id, message_id)
    elif callback_data == "new_order":
        handle_new_order_callback(user_id, message_id)
    elif callback_data == "my_orders":
        handle_my_orders_callback(user_id, message_id)
    elif callback_data == "my_assigned_orders":
        handle_my_assigned_orders_callback(user_id, message_id)
    elif callback_data == "all_orders":
        handle_all_orders_callback(user_id, message_id)
    elif callback_data == "manage_users":
        handle_manage_users_callback(user_id, message_id)
    elif callback_data == "list_users":
        handle_list_users_callback(user_id, message_id)
    elif callback_data == "approval_requests":
        handle_approval_requests_callback(user_id, message_id)
    elif callback_data.startswith("approve_"):
        user_to_approve = int(callback_data.split("_")[1])
        handle_approve_user_callback(user_id, message_id, user_to_approve)
    elif callback_data.startswith("reject_"):
        user_to_reject = int(callback_data.split("_")[1])
        handle_reject_user_callback(user_id, message_id, user_to_reject)
    elif callback_data == "add_admin":
        handle_add_admin_callback(user_id, message_id)
    elif callback_data == "add_dispatcher":
        handle_add_dispatcher_callback(user_id, message_id)
    elif callback_data == "add_technician":
        handle_add_technician_callback(user_id, message_id)
    elif callback_data.startswith("order_"):
        order_id = int(callback_data.split("_")[1])
        handle_order_detail_callback(user_id, message_id, order_id)
    elif callback_data.startswith("change_status_"):
        order_id = int(callback_data.split("_")[2])
        handle_change_status_callback(user_id, message_id, order_id)
    elif callback_data.startswith("status_"):
        parts = callback_data.split("_")
        order_id = int(parts[1])
        status = parts[2]
        handle_update_status_callback(user_id, message_id, order_id, status)
    elif callback_data.startswith("assign_technician_"):
        order_id = int(callback_data.split("_")[2])
        handle_assign_technician_callback(user_id, message_id, order_id)
    elif callback_data.startswith("assign_"):
        parts = callback_data.split("_")
        order_id = int(parts[1])
        technician_id = int(parts[2])
        handle_assign_order_callback(user_id, message_id, order_id, technician_id)
    elif callback_data.startswith("add_cost_"):
        order_id = int(callback_data.split("_")[2])
        handle_add_cost_callback(user_id, message_id, order_id)
    elif callback_data.startswith("add_description_"):
        order_id = int(callback_data.split("_")[2])
        handle_add_description_callback(user_id, message_id, order_id)
    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")

# Обработчики callback-запросов
def handle_main_menu_callback(user_id, message_id):
    """
    Обработчик callback-запроса main_menu
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Очищаем состояние пользователя
    clear_user_state(user_id)
    
    # Формируем сообщение в зависимости от роли
    if user.is_admin():
        message_text = f"Здравствуйте, {user.get_full_name()}!\nВы вошли как *Администратор*.\n\nВыберите действие:"
    elif user.is_dispatcher():
        message_text = f"Здравствуйте, {user.get_full_name()}!\nВы вошли как *Диспетчер*.\n\nВыберите действие:"
    elif user.is_technician():
        message_text = f"Здравствуйте, {user.get_full_name()}!\nВы вошли как *Техник*.\n\nВыберите действие:"
    else:
        message_text = f"Здравствуйте, {user.get_full_name()}!\n\nВыберите действие:"
    
    # Редактируем сообщение с новой клавиатурой
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=message_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode="Markdown"
    )

def handle_help_callback(user_id, message_id):
    """
    Обработчик callback-запроса help
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Формируем текст справки (аналогично обработчику команды /help)
    help_text = "🔍 *Справка по использованию бота*\n\n"
    
    # Общие команды для всех пользователей
    help_text += "*Общие команды:*\n"
    help_text += "/start - Начать работу с ботом\n"
    help_text += "/help - Показать эту справку\n\n"
    
    # Специфичные команды в зависимости от роли
    if user.is_admin():
        help_text += "*Команды администратора:*\n"
        help_text += "/all_orders - Просмотр всех заказов\n"
        help_text += "/manage_users - Управление пользователями\n"
        help_text += "\nКак администратор, вы можете:\n"
        help_text += "• Просматривать все заказы\n"
        help_text += "• Подтверждать новых пользователей\n"
        help_text += "• Назначать мастеров на заказы\n"
        help_text += "• Изменять статусы заказов\n"
        help_text += "• Добавлять новых администраторов и диспетчеров\n"
    elif user.is_dispatcher():
        help_text += "*Команды диспетчера:*\n"
        help_text += "/new_order - Создать новый заказ\n"
        help_text += "/my_orders - Просмотр созданных вами заказов\n"
        help_text += "\nКак диспетчер, вы можете:\n"
        help_text += "• Создавать новые заказы\n"
        help_text += "• Просматривать и редактировать созданные вами заказы\n"
    elif user.is_technician():
        help_text += "*Команды мастера:*\n"
        help_text += "/my_assigned_orders - Просмотр назначенных вам заказов\n"
        help_text += "\nКак техник, вы можете:\n"
        help_text += "• Просматривать назначенные вам заказы\n"
        help_text += "• Обновлять статус заказов\n"
        help_text += "• Добавлять стоимость выполненных работ\n"
        help_text += "• Добавлять описание выполненных работ\n"
    
    help_text += "\n*Работа с заказами:*\n"
    help_text += "• Создание заказа: указываются данные клиента и описание проблемы\n"
    help_text += "• Статусы заказов: новый → назначен → в работе → завершен\n"
    help_text += "• Для быстрого перехода к заказу используйте команду /order_<номер>\n"
    
    # Добавляем кнопку возврата в главное меню
    keyboard = get_back_to_main_menu_keyboard()
    
    # Редактируем сообщение с текстом справки
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=help_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_new_order_callback(user_id, message_id):
    """
    Обработчик callback-запроса new_order
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь диспетчером или администратором
    if not (user.is_dispatcher() or user.is_admin()):
        bot.send_message(
            user_id,
            "Эта функция доступна только для диспетчеров и администраторов."
        )
        return
    
    # Редактируем сообщение с инструкцией по созданию заказа
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text="📝 *Создание нового заказа*\n\n"
        "Введите номер телефона клиента:",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_phone")

def handle_my_orders_callback(user_id, message_id):
    """
    Обработчик callback-запроса my_orders
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь диспетчером или администратором
    if not (user.is_dispatcher() or user.is_admin()):
        bot.send_message(
            user_id,
            "Эта функция доступна только для диспетчеров и администраторов."
        )
        return
    
    # Получаем заказы пользователя
    orders = get_orders_by_user(user_id)
    
    # Форматируем список заказов и получаем клавиатуру
    message_text, keyboard = format_orders_list(orders)
    
    # Редактируем сообщение со списком заказов
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_my_assigned_orders_callback(user_id, message_id):
    """
    Обработчик callback-запроса my_assigned_orders
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь мастером
    if not user.is_technician():
        bot.send_message(
            user_id,
            "Эта функция доступна только для мастеров."
        )
        return
    
    # Получаем назначенные заказы
    orders = get_assigned_orders(user_id)
    
    # Форматируем список заказов и получаем клавиатуру
    message_text, keyboard = format_orders_list(orders)
    
    # Редактируем сообщение со списком заказов
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_all_orders_callback(user_id, message_id):
    """
    Обработчик callback-запроса all_orders
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Получаем все заказы
    orders = get_all_orders()
    
    # Форматируем список заказов и получаем клавиатуру
    message_text, keyboard = format_orders_list(orders)
    
    # Редактируем сообщение со списком заказов
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_manage_users_callback(user_id, message_id):
    """
    Обработчик callback-запроса manage_users
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Редактируем сообщение с клавиатурой управления пользователями
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text="👥 *Управление пользователями*\n\n"
        "Выберите действие:",
        reply_markup=get_user_management_keyboard(),
        parse_mode="Markdown"
    )

def handle_list_users_callback(user_id, message_id):
    """
    Обработчик callback-запроса list_users
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Получаем всех пользователей
    users = get_all_users()
    
    # Формируем текст сообщения со списком пользователей
    message_text = "👥 *Список пользователей*\n\n"
    
    admins = []
    dispatchers = []
    technicians = []
    
    for u in users:
        username_info = f" (@{u.username})" if u.username else ""
        status = "✅" if u.is_approved else "⌛"
        user_info = f"{status} {u.get_full_name()}{username_info} - ID: {u.user_id}\n"
        
        if u.is_admin():
            admins.append(user_info)
        elif u.is_dispatcher():
            dispatchers.append(user_info)
        elif u.is_technician():
            technicians.append(user_info)
    
    # Добавляем администраторов
    if admins:
        message_text += "*Администраторы:*\n"
        for admin in admins:
            message_text += admin
        message_text += "\n"
    
    # Добавляем диспетчеров
    if dispatchers:
        message_text += "*Диспетчеры:*\n"
        for dispatcher in dispatchers:
            message_text += dispatcher
        message_text += "\n"
    
    # Добавляем мастеров
    if technicians:
        message_text += "*Техники:*\n"
        for technician in technicians:
            message_text += technician
        message_text += "\n"
    
    # Добавляем кнопку возврата к управлению пользователями
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("◀️ Назад", callback_data="manage_users"))
    
    # Редактируем сообщение со списком пользователей
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_approval_requests_callback(user_id, message_id):
    """
    Обработчик callback-запроса approval_requests
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Получаем сообщение и клавиатуру для запросов на подтверждение
    message_text, keyboard = get_approval_requests_keyboard()
    
    # Редактируем сообщение со списком запросов
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_approve_user_callback(user_id, message_id, user_to_approve):
    """
    Обработчик подтверждения пользователя
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Подтверждаем пользователя
    if approve_user(user_to_approve):
        # Получаем информацию о подтвержденном пользователе
        approved_user = get_user(user_to_approve)
        
        if approved_user:
            # Отправляем уведомление пользователю о подтверждении
            bot.send_message(
                user_to_approve,
                f"✅ Ваша учетная запись подтверждена администратором.\n\n"
                f"Вы зарегистрированы как: *{approved_user.role.capitalize()}*\n\n"
                f"Теперь вы можете использовать все функции бота.",
                parse_mode="Markdown"
            )
            
            # Получаем обновленный список запросов на подтверждение
            message_text, keyboard = get_approval_requests_keyboard()
            
            # Редактируем сообщение
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            # Отправляем подтверждение администратору
            bot.answer_callback_query(
                callback_query_id=user_id,
                text=f"Пользователь {approved_user.get_full_name()} успешно подтвержден."
            )
        else:
            bot.answer_callback_query(
                callback_query_id=user_id,
                text="Ошибка при получении информации о пользователе."
            )
    else:
        bot.answer_callback_query(
            callback_query_id=user_id,
            text="Ошибка при подтверждении пользователя."
        )

def handle_reject_user_callback(user_id, message_id, user_to_reject):
    """
    Обработчик отклонения пользователя
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Получаем информацию о пользователе перед удалением
    rejected_user = get_user(user_to_reject)
    
    # Отклоняем пользователя
    if reject_user(user_to_reject):
        if rejected_user:
            # Отправляем уведомление пользователю об отклонении
            try:
                bot.send_message(
                    user_to_reject,
                    "❌ Ваша учетная запись была отклонена администратором.\n\n"
                    "Если вы считаете, что произошла ошибка, пожалуйста, свяжитесь с администратором."
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления отклоненному пользователю: {e}")
        
        # Получаем обновленный список запросов на подтверждение
        message_text, keyboard = get_approval_requests_keyboard()
        
        # Редактируем сообщение
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Отправляем подтверждение администратору
        user_name = rejected_user.get_full_name() if rejected_user else "Пользователь"
        bot.answer_callback_query(
            callback_query_id=user_id,
            text=f"{user_name} был отклонен."
        )
    else:
        bot.answer_callback_query(
            callback_query_id=user_id,
            text="Ошибка при отклонении пользователя."
        )

def handle_add_admin_callback(user_id, message_id):
    """
    Обработчик callback-запроса add_admin
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Редактируем сообщение с инструкцией
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text="👤 *Добавление администратора*\n\n"
        "Введите ID пользователя для назначения администратором:",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_admin_id")

def handle_add_dispatcher_callback(user_id, message_id):
    """
    Обработчик callback-запроса add_dispatcher
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Редактируем сообщение с инструкцией
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text="👤 *Добавление диспетчера*\n\n"
        "Введите ID пользователя для назначения диспетчером:",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_dispatcher_id")

def handle_add_technician_callback(user_id, message_id):
    """
    Обработчик callback-запроса add_technician
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором
    if not user.is_admin():
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов."
        )
        return
    
    # Редактируем сообщение с инструкцией
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text="👤 *Добавление мастера*\n\n"
        "Введите ID пользователя для назначения мастером:",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_technician_id")

def handle_order_detail_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса order_{order_id}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Формируем сообщение с информацией о заказе
    message_text = order.format_for_display()
    
    # Определяем тип клавиатуры в зависимости от роли пользователя
    keyboard = None
    if user.is_admin():
        keyboard = get_order_management_keyboard(order_id)
    elif user.is_dispatcher() and order.dispatcher_id == user_id:
        keyboard = get_order_management_keyboard(order_id)
    elif user.is_technician():
        # Проверяем, назначен ли заказ этому мастеру
        technicians = get_order_technicians(order_id)
        is_assigned = any(tech.technician_id == user_id for tech in technicians)
        
        if is_assigned:
            keyboard = get_technician_order_keyboard(order_id)
        else:
            keyboard = get_back_to_main_menu_keyboard()
    else:
        keyboard = get_back_to_main_menu_keyboard()
    
    # Редактируем сообщение
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        # Если текст слишком длинный или другие проблемы, пробуем отправить без разметки
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=message_text,
                reply_markup=keyboard
            )
        except Exception as e2:
            logger.error(f"Ошибка при редактировании сообщения с заказом: {e2}")
            bot.send_message(
                user_id,
                "Произошла ошибка при отображении информации о заказе."
            )

def handle_change_status_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса change_status_{order_id}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Редактируем сообщение с клавиатурой для изменения статуса
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"🔄 *Изменение статуса заказа #{order_id}*\n\n"
        f"Текущий статус: *{order.status_to_russian()}*\n\n"
        "Выберите новый статус:",
        reply_markup=get_order_status_keyboard(order_id),
        parse_mode="Markdown"
    )

def handle_update_status_callback(user_id, message_id, order_id, status):
    """
    Обработчик callback-запроса status_{order_id}_{status}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Обновляем статус заказа
    if update_order(order_id, status=status):
        # Получаем обновленную информацию о заказе
        updated_order = get_order(order_id)
        
        # Формируем сообщение с информацией о заказе
        message_text = updated_order.format_for_display() if updated_order else "❌ Ошибка при получении информации о заказе."
        
        # Определяем тип клавиатуры в зависимости от роли пользователя
        keyboard = None
        if user.is_admin():
            keyboard = get_order_management_keyboard(order_id)
        elif user.is_dispatcher() and order.dispatcher_id == user_id:
            keyboard = get_order_management_keyboard(order_id)
        elif user.is_technician():
            keyboard = get_technician_order_keyboard(order_id)
        else:
            keyboard = get_back_to_main_menu_keyboard()
        
        # Редактируем сообщение
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Отправляем уведомление о изменении статуса
        if updated_order and order.status != status:
            # Получаем всех мастеров заказа
            technicians = get_order_technicians(order_id)
            
            # Отправляем уведомление мастерам
            for tech in technicians:
                if tech.technician_id != user_id:  # Не отправляем уведомление тому, кто обновил статус
                    try:
                        bot.send_message(
                            tech.technician_id,
                            f"🔄 *Обновление статуса заказа #{order_id}*\n\n"
                            f"Статус изменен на: *{updated_order.status_to_russian()}*\n\n"
                            "Используйте команду /my_assigned_orders для просмотра ваших заказов.",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления мастеру {tech.technician_id}: {e}")
            
            # Отправляем уведомление диспетчеру
            if updated_order.dispatcher_id and updated_order.dispatcher_id != user_id:
                try:
                    bot.send_message(
                        updated_order.dispatcher_id,
                        f"🔄 *Обновление статуса заказа #{order_id}*\n\n"
                        f"Статус изменен на: *{updated_order.status_to_russian()}*\n\n"
                        "Используйте команду /my_orders для просмотра ваших заказов.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления диспетчеру {updated_order.dispatcher_id}: {e}")
    else:
        bot.answer_callback_query(
            call.id,
            "Ошибка при обновлении статуса заказа."
        )

def handle_assign_technician_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса assign_technician_{order_id}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором или диспетчером
    if not (user.is_admin() or user.is_dispatcher()):
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов и диспетчеров."
        )
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Получаем клавиатуру со списком мастеров
    keyboard = get_technician_list_keyboard(order_id)
    
    # Редактируем сообщение
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"👤 *Назначение мастера на заказ #{order_id}*\n\n"
        "Выберите мастера из списка:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_assign_order_callback(user_id, message_id, order_id, technician_id):
    """
    Обработчик callback-запроса assign_{order_id}_{technician_id}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Проверяем, является ли пользователь администратором или диспетчером
    if not (user.is_admin() or user.is_dispatcher()):
        bot.send_message(
            user_id,
            "Эта функция доступна только для администраторов и диспетчеров."
        )
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Получаем информацию о технике
    technician = get_user(technician_id)
    
    if not technician:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Техник с указанным ID не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Назначаем мастера на заказ
    assignment_id = assign_order(order_id, technician_id, user_id)
    
    if assignment_id:
        # Получаем обновленную информацию о заказе
        updated_order = get_order(order_id)
        
        # Формируем сообщение с информацией о заказе
        message_text = updated_order.format_for_display() if updated_order else "❌ Ошибка при получении информации о заказе."
        
        # Получаем клавиатуру для управления заказом
        keyboard = get_order_management_keyboard(order_id)
        
        # Редактируем сообщение
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Отправляем уведомление мастеру о назначении
        try:
            bot.send_message(
                technician_id,
                f"📋 *Новый заказ назначен*\n\n"
                f"Вы были назначены на заказ #{order_id}.\n\n"
                "Используйте команду /my_assigned_orders для просмотра ваших заказов.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления мастеру {technician_id}: {e}")
    else:
        bot.answer_callback_query(
            call.id,
            "Ошибка при назначении мастера на заказ."
        )

def handle_add_cost_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса add_cost_{order_id}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Редактируем сообщение с инструкцией
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"💰 *Добавление стоимости для заказа #{order_id}*\n\n"
        f"Текущая стоимость: {order.service_cost if order.service_cost is not None else 'Не указана'}\n\n"
        "Введите стоимость услуг (только число):",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_cost", order_id)

def handle_add_description_callback(user_id, message_id, order_id):
    """
    Обработчик callback-запроса add_description_{order_id}
    """
    user = get_user(user_id)
    
    if not user:
        return
    
    # Получаем информацию о заказе
    order = get_order(order_id)
    
    if not order:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Заказ с указанным номером не найден.",
            reply_markup=get_back_to_main_menu_keyboard()
        )
        return
    
    # Редактируем сообщение с инструкцией
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"📝 *Добавление описания для заказа #{order_id}*\n\n"
        f"Текущее описание: {order.service_description if order.service_description else 'Не указано'}\n\n"
        "Введите описание выполненных работ:",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, "waiting_for_description", order_id)

# Обработчик всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Обработчик всех текстовых сообщений
    """
    user_id = message.from_user.id
    text = message.text
    
    # Получаем пользователя из БД
    user = get_user(user_id)
    
    if not user:
        bot.reply_to(
            message,
            "Ваша учетная запись не найдена. Пожалуйста, используйте команду /start для регистрации."
        )
        return
    
    # Получаем текущее состояние пользователя
    state = get_user_state(user_id)
    
    if not state:
        # Если нет состояния, отправляем общее сообщение
        bot.reply_to(
            message,
            "Используйте команды или кнопки для взаимодействия с ботом.\n"
            "Отправьте /help для получения справки."
        )
        return
    
    # Обрабатываем состояния пользователя
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
        # Неизвестное состояние
        bot.reply_to(
            message,
            "Используйте команды или кнопки для взаимодействия с ботом.\n"
            "Отправьте /help для получения справки."
        )
        # Очищаем неизвестное состояние
        clear_user_state(user_id)

def handle_phone_input(user_id, text):
    """
    Обработка ввода номера телефона
    """
    # Проверяем формат номера телефона
    if not validate_phone(text):
        bot.send_message(
            user_id,
            "❌ Неверный формат номера телефона. Пожалуйста, введите корректный номер."
        )
        return
    
    # Сохраняем номер телефона
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['phone'] = text
    
    # Запрашиваем имя клиента
    bot.send_message(
        user_id,
        "👤 Введите имя клиента:"
    )
    
    # Обновляем состояние пользователя
    set_user_state(user_id, "waiting_for_name")

def handle_name_input(user_id, text):
    """
    Обработка ввода имени клиента
    """
    # Сохраняем имя клиента
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['name'] = text
    
    # Запрашиваем адрес клиента
    bot.send_message(
        user_id,
        "🏠 Введите адрес клиента:"
    )
    
    # Обновляем состояние пользователя
    set_user_state(user_id, "waiting_for_address")

def handle_address_input(user_id, text):
    """
    Обработка ввода адреса клиента
    """
    # Сохраняем адрес клиента
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['address'] = text
    
    # Запрашиваем описание проблемы
    bot.send_message(
        user_id,
        "🔧 Введите описание проблемы:"
    )
    
    # Обновляем состояние пользователя
    set_user_state(user_id, "waiting_for_problem")

def handle_problem_input(user_id, text):
    """
    Обработка ввода описания проблемы
    """
    # Сохраняем описание проблемы
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['problem'] = text
    
    # Создаем заказ
    try:
        order_id = save_order(
            user_id,
            user_data[user_id]['phone'],
            user_data[user_id]['name'],
            user_data[user_id]['address'],
            user_data[user_id]['problem']
        )
        
        if order_id:
            # Получаем информацию о заказе
            order = get_order(order_id)
            
            if order:
                # Отправляем подтверждение создания заказа
                bot.send_message(
                    user_id,
                    f"✅ *Заказ успешно создан*\n\n"
                    f"Номер заказа: *#{order_id}*\n\n"
                    f"{order.format_for_display()}",
                    reply_markup=get_main_menu_keyboard(user_id),
                    parse_mode="Markdown"
                )
                
                # Отправляем уведомление администраторам
                send_order_notification_to_admins(bot, order_id)
            else:
                bot.send_message(
                    user_id,
                    "✅ Заказ успешно создан, но произошла ошибка при получении информации о нем.",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        else:
            bot.send_message(
                user_id,
                "❌ Произошла ошибка при создании заказа. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except Exception as e:
        logger.error(f"Ошибка при создании заказа: {e}")
        bot.send_message(
            user_id,
            "❌ Произошла ошибка при создании заказа. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    finally:
        # Очищаем данные пользователя и состояние
        if user_id in user_data:
            del user_data[user_id]
        clear_user_state(user_id)

def handle_user_id_input(user_id, text, role):
    """
    Обработка ввода ID пользователя для назначения роли
    """
    try:
        # Преобразуем ID в число
        target_user_id = int(text)
        
        # Получаем пользователя по ID
        target_user = get_user(target_user_id)
        
        if not target_user:
            bot.send_message(
                user_id,
                "❌ Пользователь с указанным ID не найден. Пожалуйста, убедитесь, что пользователь начал взаимодействие с ботом.",
                reply_markup=get_user_management_keyboard()
            )
            clear_user_state(user_id)
            return
        
        # Обновляем роль пользователя
        if update_user_role(target_user_id, role):
            # Подтверждаем пользователя, если он не был подтвержден
            if not target_user.is_approved:
                approve_user(target_user_id)
            
            # Отправляем подтверждение об обновлении роли
            role_name = "администратора" if role == "admin" else "диспетчера" if role == "dispatcher" else "мастера"
            bot.send_message(
                user_id,
                f"✅ Пользователь {target_user.get_full_name()} успешно назначен на роль {role_name}.",
                reply_markup=get_user_management_keyboard()
            )
            
            # Отправляем уведомление пользователю
            try:
                bot.send_message(
                    target_user_id,
                    f"✅ Вам назначена новая роль: *{role.capitalize()}*\n\n"
                    f"Теперь вы можете использовать все функции, доступные для этой роли.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
        else:
            bot.send_message(
                user_id,
                "❌ Произошла ошибка при обновлении роли пользователя. Пожалуйста, попробуйте позже.",
                reply_markup=get_user_management_keyboard()
            )
    except ValueError:
        bot.send_message(
            user_id,
            "❌ Некорректный ID пользователя. Пожалуйста, введите число.",
            reply_markup=get_user_management_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке ID пользователя: {e}")
        bot.send_message(
            user_id,
            "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_management_keyboard()
        )
    finally:
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
            "❌ Ошибка: ID заказа не найден. Пожалуйста, попробуйте снова.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        clear_user_state(user_id)
        return
    
    try:
        # Преобразуем стоимость в число
        cost = float(text.replace(',', '.'))
        
        # Проверяем, что стоимость положительная
        if cost < 0:
            bot.send_message(
                user_id,
                "❌ Стоимость не может быть отрицательной. Пожалуйста, введите положительное число."
            )
            return
        
        # Обновляем стоимость услуг в заказе
        if update_order(order_id, service_cost=cost):
            # Получаем обновленную информацию о заказе
            order = get_order(order_id)
            
            if order:
                # Отправляем подтверждение обновления стоимости
                bot.send_message(
                    user_id,
                    f"✅ Стоимость услуг для заказа #{order_id} успешно обновлена.\n\n"
                    f"{order.format_for_display()}",
                    reply_markup=get_technician_order_keyboard(order_id),
                    parse_mode="Markdown"
                )
                
                # Отправляем уведомление диспетчеру
                if order.dispatcher_id and order.dispatcher_id != user_id:
                    try:
                        bot.send_message(
                            order.dispatcher_id,
                            f"💰 *Обновлена стоимость заказа #{order_id}*\n\n"
                            f"Стоимость: {cost} руб.\n\n"
                            "Используйте команду /my_orders для просмотра ваших заказов.",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления диспетчеру {order.dispatcher_id}: {e}")
            else:
                bot.send_message(
                    user_id,
                    "✅ Стоимость услуг успешно обновлена, но произошла ошибка при получении информации о заказе.",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        else:
            bot.send_message(
                user_id,
                "❌ Произошла ошибка при обновлении стоимости услуг. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except ValueError:
        bot.send_message(
            user_id,
            "❌ Некорректный формат стоимости. Пожалуйста, введите число (например, 1500 или 1500.50)."
        )
        return
    except Exception as e:
        logger.error(f"Ошибка при обработке стоимости услуг: {e}")
        bot.send_message(
            user_id,
            "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    finally:
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
            "❌ Ошибка: ID заказа не найден. Пожалуйста, попробуйте снова.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        clear_user_state(user_id)
        return
    
    try:
        # Обновляем описание выполненных работ в заказе
        if update_order(order_id, service_description=text):
            # Получаем обновленную информацию о заказе
            order = get_order(order_id)
            
            if order:
                # Отправляем подтверждение обновления описания
                bot.send_message(
                    user_id,
                    f"✅ Описание выполненных работ для заказа #{order_id} успешно обновлено.\n\n"
                    f"{order.format_for_display()}",
                    reply_markup=get_technician_order_keyboard(order_id),
                    parse_mode="Markdown"
                )
                
                # Отправляем уведомление диспетчеру
                if order.dispatcher_id and order.dispatcher_id != user_id:
                    try:
                        bot.send_message(
                            order.dispatcher_id,
                            f"📝 *Обновлено описание работ для заказа #{order_id}*\n\n"
                            f"Описание: {text}\n\n"
                            "Используйте команду /my_orders для просмотра ваших заказов.",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления диспетчеру {order.dispatcher_id}: {e}")
            else:
                bot.send_message(
                    user_id,
                    "✅ Описание выполненных работ успешно обновлено, но произошла ошибка при получении информации о заказе.",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        else:
            bot.send_message(
                user_id,
                "❌ Произошла ошибка при обновлении описания выполненных работ. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке описания выполненных работ: {e}")
        bot.send_message(
            user_id,
            "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    finally:
        # Очищаем состояние пользователя
        clear_user_state(user_id)