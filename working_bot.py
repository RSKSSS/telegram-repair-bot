#!/usr/bin/env python
"""
Прямой запуск полной версии бота без промежуточных файлов
"""

import os
import logging
import sys
import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка наличия токена бота
token = os.environ.get('TELEGRAM_BOT_TOKEN')
if not token:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

logger.info(f"Токен получен (длина: {len(token)})")
logger.info("Запуск полной версии бота...")

# Импорт всех необходимых модулей перед запуском
try:
    import datetime
    from telebot import types
    from config import ROLES, ORDER_STATUSES
    from ui_constants import EMOJI, STATUS_NAMES  # Добавляем STATUS_NAMES
    from database import (
        save_user, get_all_users, get_user_role, is_user_approved,
        get_unapproved_users, approve_user, reject_user, update_user_role,
        save_order, update_order, get_orders_by_user, get_all_orders,
        get_assigned_orders, assign_order, get_technicians, get_order_technicians,
        set_user_state, get_user_state, get_current_order_id, clear_user_state,
        save_problem_template, update_problem_template, get_problem_template,
        get_problem_templates, delete_problem_template, delete_user, delete_order,
        add_activity_log, get_activity_logs, get_admin_activity_summary, update_order_status
    )
    from database import get_user  # Отдельный импорт из-за проблем с использованием
    from database import get_order  # Отдельный импорт из-за проблем с использованием
    from utils import (
        get_main_menu_keyboard, get_order_status_keyboard, get_order_management_keyboard,
        get_back_to_orders_keyboard,
        get_technician_order_keyboard, get_back_to_main_menu_keyboard, get_approval_requests_keyboard,
        get_user_management_keyboard, is_admin, is_dispatcher, is_technician,
        send_order_notification_to_admins, validate_phone, format_orders_list, get_technician_list_keyboard,
        get_role_name, get_user_list_for_deletion, get_order_list_for_deletion
    )
    from shared_state import bot
    from telebot import types
    from ai_commands import (
        register_ai_commands, handle_cancel_command
    )
    
    logger.info("Все модули успешно импортированы")
except ImportError as e:
    logger.error(f"Ошибка при импорте модулей: {e}")
    sys.exit(1)

# Определение вспомогательных функций
def get_status_name(status_code):
    """
    Возвращает читаемое имя статуса по коду
    
    Args:
        status_code: Код статуса заказа
    
    Returns:
        str: Человекочитаемое название статуса
    """
    return ORDER_STATUSES.get(status_code, status_code.capitalize())

def get_full_name(user):
    """
    Форматирует полное имя пользователя
    """
    first_name = user.get('first_name', '')
    last_name = user.get('last_name', '')
    
    if first_name and last_name:
        return f"{first_name} {last_name}"
    return first_name or last_name or "Пользователь"

def updated_format_orders_list(orders, include_details=True):
    """
    Форматирует список заказов для отображения
    """
    if not orders:
        return "📋 Список заказов пуст"
    
    result = "📋 *Список заказов:*\n\n"
    
    for order in orders:
        order_id = order.get('order_id', 'Нет ID')
        status = order.get('status', 'Нет статуса')
        status_emoji = {
            'new': '🆕',
            'in_progress': '🔄',
            'completed': '✅',
            'cancelled': '❌'
        }.get(status, '❓')
        
        client_name = order.get('client_name', 'Нет имени')
        problem_description = order.get('problem_description', 'Нет описания')
        
        # Короткое описание для списка
        short_desc = problem_description[:50] + "..." if len(problem_description) > 50 else problem_description
        
        result += f"{status_emoji} *Заказ #{order_id}* - {client_name}\n"
        result += f"Статус: *{ORDER_STATUSES.get(status, status)}*\n"
        
        if include_details:
            result += f"Описание: {short_desc}\n"
            
            # Информация о мастере
            technician_id = order.get('technician_id')
            if technician_id:
                try:
                    technician = get_user(technician_id)
                    if technician:
                        tech_name = get_full_name(technician)
                        result += f"Мастер: {tech_name}\n"
                except Exception as e:
                    result += "Мастер: Ошибка получения данных\n"
        
        result += "\n"
    
    return result

# Регистрация обработчиков команд бота

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    """
    Обработчик команды /start
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    username = message.from_user.username

    try:
        # Сохраняем информацию о пользователе в БД
        save_user(user_id, first_name, last_name, username)

        # Получаем актуальную информацию о пользователе
        user = get_user(user_id)

        if not user:
            bot.reply_to(message, "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
            return

        greeting = f"Здравствуйте, {first_name}!"
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        bot.reply_to(message, "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        return

    if user['is_approved']:
        # Создаем постоянную клавиатуру с командами
        from utils import get_reply_keyboard
        reply_keyboard = get_reply_keyboard(user_id)

        if is_admin(user_id):
            bot.send_message(
                user_id,
                f"{greeting}\nВы вошли как *Администратор*.\n\nВыберите действие:",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            # Отправляем еще одно сообщение с inline-кнопками для быстрого доступа
            bot.send_message(
                user_id,
                "📲 *Быстрый доступ к функциям:*",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
        elif is_dispatcher(user_id):
            bot.send_message(
                user_id,
                f"{greeting}\nВы вошли как *Диспетчер*.\n\nВыберите действие:",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            # Отправляем еще одно сообщение с inline-кнопками для быстрого доступа
            bot.send_message(
                user_id,
                "📲 *Быстрый доступ к функциям:*",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
        elif is_technician(user_id):
            bot.send_message(
                user_id,
                f"{greeting}\nВы вошли как *Мастер*.\n\nВыберите действие:",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            # Отправляем еще одно сообщение с inline-кнопками для быстрого доступа
            bot.send_message(
                user_id,
                "📲 *Быстрый доступ к функциям:*",
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
        admins = [user for user in get_all_users() if user['role'] == 'admin']

        if admins:
            username_info = f" (@{username})" if username else ""
            notification = (
                f"🔔 Новый пользователь в системе\n\n"
                f"👤 {first_name} {last_name or ''}{username_info}\n"
                f"🆔 ID: {user_id}\n\n"
            )

            # Создаем инлайн клавиатуру с кнопками принять/отказать
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(row_width=2)
            approve_button = InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{user_id}")
            reject_button = InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{user_id}")
            keyboard.add(approve_button, reject_button)
            keyboard.add(InlineKeyboardButton(text="👥 Управление пользователями", callback_data="manage_users"))

            for admin in admins:
                try:
                    bot.send_message(admin['user_id'], notification, reply_markup=keyboard)
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления администратору {admin['user_id']}: {e}")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def handle_help_command(message):
    """
    Обработчик команды /help
    """
    user_id = message.from_user.id

    # Получаем пользователя из БД
    user = get_user(user_id)

    if not user or not user['is_approved']:
        bot.reply_to(
            message,
            "Ваша учетная запись не подтверждена администратором. "
            "Пожалуйста, дождитесь подтверждения."
        )
        return

    # Формируем текст справки в зависимости от роли пользователя
    help_text = "🔍 Справка по использованию бота\n\n"

    # Общие команды для всех пользователей
    help_text += "Общие команды:\n"
    help_text += "/start - Начать работу с ботом\n"
    help_text += "/help - Показать эту справку\n\n"

    # Специфичные команды в зависимости от роли
    if is_admin(user_id):
        help_text += "Команды администратора:\n"
        help_text += "/all_orders - Просмотр всех заказов\n"
        help_text += "/manage_users - Управление пользователями\n"
        help_text += "/add_template - Добавить шаблон проблемы\n"
        help_text += "/templates - Управление шаблонами проблем\n"
        help_text += "/activity_log - Просмотр лога активности\n"
    elif is_dispatcher(user_id):
        help_text += "Команды диспетчера:\n"
        help_text += "/new_order - Создать новый заказ\n"
        help_text += "/all_orders - Просмотр всех заказов\n"
        help_text += "/assign_order - Назначить заказ мастеру\n"
        help_text += "/add_template - Добавить шаблон проблемы\n"
        help_text += "/templates - Управление шаблонами проблем\n"
    elif is_technician(user_id):
        help_text += "Команды мастера:\n"
        help_text += "/my_orders - Просмотр назначенных вам заказов\n"
        help_text += "/update_status - Обновить статус заказа\n"

    # Отправляем справку
    bot.send_message(user_id, help_text)

# Обработчик команды /manage_users (только для администраторов)
@bot.message_handler(commands=['manage_users'])
def handle_manage_users_command(message):
    """
    Обработчик команды /manage_users
    Показывает меню управления пользователями (только для администраторов)
    """
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ У вас нет прав для выполнения этой команды.")
        return
    
    keyboard = get_user_management_keyboard()
    bot.send_message(
        user_id, 
        "👥 *Управление пользователями*\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Обработчик команды /info для проверки работоспособности
@bot.message_handler(commands=['info'])
def handle_info_command(message):
    """
    Обработчик команды /info
    Выводит информацию о системе для отладки
    """
    user_id = message.from_user.id
    
    # Получаем информацию о пользователе
    user = get_user(user_id)
    
    # Формируем информационное сообщение
    info_text = "📊 *Информация о системе*\n\n"
    
    if user:
        info_text += f"👤 *Пользователь:* {user.get('first_name')} {user.get('last_name') or ''}\n"
        info_text += f"🆔 ID: `{user_id}`\n"
        info_text += f"👑 Роль: {get_role_name(user.get('role', 'user'))}\n"
        info_text += f"✅ Подтвержден: {'Да' if user.get('is_approved') else 'Нет'}\n\n"
    else:
        info_text += "❌ Пользователь не найден в базе данных\n\n"
    
    # Информация о системе
    import platform
    info_text += f"🖥️ *Система:*\n"
    info_text += f"ОС: {platform.system()} {platform.release()}\n"
    info_text += f"Python: {platform.python_version()}\n"
    
    # Информация о базе данных
    try:
        users_count = len(get_all_users())
        orders_count = len(get_all_orders())
        info_text += f"\n📝 *База данных:*\n"
        info_text += f"Пользователей: {users_count}\n"
        info_text += f"Заказов: {orders_count}\n"
    except Exception as e:
        info_text += f"\n❌ *Ошибка БД:* {str(e)}\n"
    
    # Отправляем информацию
    bot.send_message(user_id, info_text, parse_mode="Markdown")

# Обработчик callback-запросов для кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """
    Обработчик всех callback-запросов от inline-кнопок
    """
    user_id = call.from_user.id
    message_id = call.message.message_id
    callback_data = call.data
    
    logger.info(f"Получен callback: {callback_data} от пользователя {user_id}")
    
    try:
        # Обработка запросов подтверждения/отклонения пользователей
        if callback_data.startswith("approve_"):
            user_id_part = callback_data.split("_")[1]
            
            # Проверяем, что ID пользователя - это число
            if user_id_part == "unknown" or not user_id_part.isdigit():
                bot.answer_callback_query(call.id, "⚠️ Не удалось определить ID пользователя")
                bot.edit_message_text(
                    "⚠️ Не удалось обработать запрос подтверждения. ID пользователя не определен.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard()
                )
                return
                
            try:
                target_user_id = int(user_id_part)
                approve_user(target_user_id)
                
                # Получаем информацию о пользователе
                target_user = get_user(target_user_id)
                user_name = f"{target_user['first_name']} {target_user.get('last_name', '')}" if target_user else str(target_user_id)
                
                # Уведомляем администратора
                bot.edit_message_text(
                    f"✅ Пользователь {user_name} подтвержден!",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode=None
                )
                
                # Уведомляем пользователя
                try:
                    bot.send_message(
                        target_user_id,
                        "✅ Ваша учетная запись подтверждена администратором! Используйте /start для начала работы.",
                        parse_mode=None
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
            except Exception as e:
                logger.error(f"Ошибка при подтверждении пользователя: {e}")
                bot.answer_callback_query(call.id, "⚠️ Ошибка при подтверждении пользователя")
                
        elif callback_data.startswith("reject_"):
            user_id_part = callback_data.split("_")[1]
            
            # Проверяем, что ID пользователя - это число
            if user_id_part == "unknown" or not user_id_part.isdigit():
                bot.answer_callback_query(call.id, "⚠️ Не удалось определить ID пользователя")
                bot.edit_message_text(
                    "⚠️ Не удалось обработать запрос отклонения. ID пользователя не определен.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard()
                )
                return
                
            try:
                target_user_id = int(user_id_part)
                reject_user(target_user_id)
                
                # Получаем информацию о пользователе
                target_user = get_user(target_user_id)
                user_name = f"{target_user['first_name']} {target_user.get('last_name', '')}" if target_user else str(target_user_id)
                
                # Уведомляем администратора
                bot.edit_message_text(
                    f"❌ Пользователь {user_name} отклонен!",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode=None
                )
                
                # Уведомляем пользователя
                try:
                    bot.send_message(
                        target_user_id,
                        "❌ Ваша учетная запись отклонена администратором."
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
            except Exception as e:
                logger.error(f"Ошибка при отклонении пользователя: {e}")
                bot.answer_callback_query(call.id, "⚠️ Ошибка при отклонении пользователя")
                
        # Обработка запросов управления пользователями
        elif callback_data == "manage_users":
            keyboard = get_user_management_keyboard()
            bot.edit_message_text(
                "👥 *Управление пользователями*\n\nВыберите действие:",
                user_id,
                message_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        elif callback_data == "approval_requests":
            # Получаем список пользователей, ожидающих подтверждения
            unapproved_users = get_unapproved_users()
            
            if not unapproved_users:
                bot.edit_message_text(
                    "👥 *Запросы на подтверждение*\n\nНет пользователей, ожидающих подтверждения.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                # Создаем клавиатуру для запросов на подтверждение
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                
                # Добавляем по кнопке для каждого неподтвержденного пользователя
                for user_data in unapproved_users:
                    user_id_str = str(user_data.get('id', 'unknown'))
                    user_name = user_data.get('first_name', 'Неизвестный')
                    
                    # Кнопки подтверждения и отклонения
                    approve_button = types.InlineKeyboardButton(
                        f"✅ Подтвердить {user_name}", 
                        callback_data=f"approve_{user_id_str}"
                    )
                    reject_button = types.InlineKeyboardButton(
                        f"❌ Отклонить {user_name}", 
                        callback_data=f"reject_{user_id_str}"
                    )
                    
                    keyboard.add(approve_button, reject_button)
                
                # Добавляем кнопку возврата
                back_button = types.InlineKeyboardButton(
                    "↩️ Назад к управлению пользователями", 
                    callback_data="manage_users"
                )
                keyboard.add(back_button)
                
                bot.edit_message_text(
                    "👥 *Запросы на подтверждение*\n\nСписок пользователей, ожидающих подтверждения:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
        # Обработка AI-запросов через модуль ai_commands
        elif callback_data.startswith("ai_"):
            bot.answer_callback_query(call.id, "ИИ-функция обрабатывается...")
            try:
                from ai_commands import (
                    handle_ai_analyze_problem_callback,
                    handle_ai_suggest_cost_callback,
                    handle_ai_generate_description_callback,
                    handle_ai_technician_help_callback,
                    handle_ai_order_help_callback,
                    handle_set_cost_callback,
                    handle_set_description_callback
                )
                
                if callback_data.startswith("ai_analyze_problem"):
                    handle_ai_analyze_problem_callback(user_id, message_id)
                
                elif callback_data.startswith("ai_suggest_cost"):
                    handle_ai_suggest_cost_callback(user_id, message_id)
                
                elif callback_data.startswith("ai_generate_description"):
                    handle_ai_generate_description_callback(user_id, message_id)
                
                elif callback_data.startswith("ai_technician_help"):
                    handle_ai_technician_help_callback(user_id, message_id)
                
                elif callback_data.startswith("ai_order_help_"):
                    order_id = int(callback_data.split("_")[-1])
                    handle_ai_order_help_callback(user_id, message_id, order_id)
                
                elif callback_data.startswith("set_cost_"):
                    parts = callback_data.split("_")
                    order_id = int(parts[2])
                    cost = float(parts[3])
                    handle_set_cost_callback(user_id, message_id, order_id, cost)
                
                elif callback_data.startswith("set_description_"):
                    order_id = int(callback_data.split("_")[-1])
                    handle_set_description_callback(user_id, message_id, order_id)
            except Exception as e:
                logger.error(f"Ошибка при обработке AI-запроса: {e}")
                bot.send_message(user_id, "⚠️ Ошибка при обработке ИИ-запроса. Попробуйте позже.")
            
        # Обработка запросов управления заказами
        elif callback_data == "all_orders":
            orders = get_all_orders()
            if not orders:
                bot.edit_message_text(
                    "📋 *Все заказы*\n\nСписок заказов пуст.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                # Создаем клавиатуру с кнопками для каждого заказа
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                
                for order in orders:
                    order_id = order.get('order_id')
                    client_name = order.get('client_name', 'Нет имени')
                    status = order.get('status', 'Нет статуса')
                    
                    # Подготавливаем подпись для кнопки
                    button_text = f"#{order_id} - {client_name} [{get_status_name(status)}]"
                    
                    # Добавляем кнопку для каждого заказа
                    keyboard.add(types.InlineKeyboardButton(
                        button_text, 
                        callback_data=f"view_order_{order_id}"
                    ))
                
                # Добавляем кнопку "Назад"
                keyboard.add(types.InlineKeyboardButton(
                    "↩️ Назад", 
                    callback_data="manage_orders"
                ))
                
                bot.edit_message_text(
                    "📋 *Список всех заказов*\n\nВыберите заказ для просмотра подробной информации:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
        # Обработка просмотра конкретного заказа
        elif callback_data.startswith("view_order_"):
            try:
                order_id = int(callback_data.split("_")[2])
                
                # Получаем информацию о заказе
                order = get_order(order_id)
                
                if not order:
                    bot.answer_callback_query(call.id, "⚠️ Заказ не найден")
                    return
                
                # Форматируем информацию о заказе
                client_name = order.get('client_name', 'Нет имени')
                client_phone = order.get('client_phone', 'Нет номера')
                problem = order.get('problem_description', 'Нет описания')
                address = order.get('client_address', 'Нет адреса')
                status = order.get('status', 'Нет статуса')
                
                order_info = (
                    f"📋 *Информация о заказе #{order_id}*\n\n"
                    f"👤 *Клиент:* {client_name}\n"
                    f"📞 *Телефон:* {client_phone}\n"
                    f"📝 *Проблема:* {problem}\n"
                    f"📍 *Адрес:* {address}\n"
                    f"🔄 *Статус:* {get_status_name(status)}\n"
                )
                
                # Проверяем, назначен ли мастер на заказ
                technician_id = order.get('technician_id')
                if technician_id:
                    technician = get_user(technician_id)
                    if technician:
                        tech_name = f"{technician.get('first_name')} {technician.get('last_name', '')}"
                        order_info += f"👨‍🔧 *Мастер:* {tech_name}\n"
                
                # Создаем клавиатуру для управления заказом
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                
                # Кнопка изменения статуса
                keyboard.add(types.InlineKeyboardButton(
                    "🔄 Изменить статус", 
                    callback_data=f"change_status_{order_id}"
                ))
                
                # Кнопка назначения мастера (только для администраторов)
                if is_admin(user_id):
                    keyboard.add(types.InlineKeyboardButton(
                        "👨‍🔧 Назначить мастера", 
                        callback_data=f"assign_technician_{order_id}"
                    ))
                
                # Кнопка назад к списку заказов
                keyboard.add(types.InlineKeyboardButton(
                    "📋 К списку заказов", 
                    callback_data="all_orders"
                ))
                
                # Кнопка возврата в главное меню
                keyboard.add(types.InlineKeyboardButton(
                    "🏠 Главное меню", 
                    callback_data="main_menu"
                ))
                
                bot.edit_message_text(
                    order_info,
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Ошибка при просмотре заказа: {e}")
                bot.answer_callback_query(call.id, "⚠️ Ошибка при просмотре заказа")
                
        # Обработка запросов назначения мастера на заказ
        elif callback_data.startswith("assign_technician_"):
            try:
                order_id = int(callback_data.split("_")[2])
                
                # Получаем информацию о заказе
                order = get_order(order_id)
                if not order:
                    bot.answer_callback_query(call.id, "⚠️ Заказ не найден")
                    return
                
                # Получаем список доступных мастеров
                technicians = [user for user in get_all_users() if user.get('role') == 'technician']
                
                if not technicians:
                    bot.answer_callback_query(call.id, "⚠️ Нет доступных мастеров")
                    bot.send_message(user_id, "⚠️ В системе нет зарегистрированных мастеров. Сначала добавьте хотя бы одного мастера.")
                    return
                
                # Создаем клавиатуру со списком мастеров
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                
                for tech in technicians:
                    tech_name = f"{tech.get('first_name')} {tech.get('last_name', '')}"
                    keyboard.add(types.InlineKeyboardButton(
                        tech_name, 
                        callback_data=f"assign_{order_id}_{tech.get('user_id')}"
                    ))
                    
                keyboard.add(types.InlineKeyboardButton(
                    "↩️ Назад", 
                    callback_data=f"view_order_{order_id}"
                ))
                
                # Отправляем сообщение с выбором мастера
                bot.edit_message_text(
                    f"👨‍🔧 *Назначение мастера на заказ #{order_id}*\n\n"
                    f"Выберите мастера из списка:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Ошибка при выборе мастера: {e}")
                bot.answer_callback_query(call.id, "⚠️ Произошла ошибка при выборе мастера")
                
        # Обработка назначения конкретного мастера на заказ
        elif callback_data.startswith("assign_"):
            try:
                parts = callback_data.split("_")
                order_id = int(parts[1])
                tech_id = int(parts[2])
                
                # Назначаем мастера на заказ
                update_order(order_id, {'technician_id': tech_id, 'status': 'assigned'})
                
                # Получаем информацию о заказе и мастере
                order = get_order(order_id)
                tech = get_user(tech_id)
                
                if not order or not tech:
                    bot.answer_callback_query(call.id, "⚠️ Не удалось получить информацию о заказе или мастере")
                    return
                
                tech_name = f"{tech.get('first_name')} {tech.get('last_name', '')}"
                
                # Уведомляем администратора об успешном назначении
                bot.edit_message_text(
                    f"✅ *Мастер успешно назначен*\n\n"
                    f"Заказ #{order_id} назначен мастеру {tech_name}",
                    user_id,
                    message_id,
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("↩️ К заказу", callback_data=f"view_order_{order_id}"),
                        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
                    ),
                    parse_mode="Markdown"
                )
                
                # Записываем информацию в лог
                try:
                    logger.info(f"Пользователь {get_full_name(get_user(user_id))} назначил мастера {tech_name} на заказ #{order_id}")
                except Exception as log_error:
                    logger.error(f"Ошибка при записи в лог: {log_error}")
                
                # Уведомляем мастера о новом назначении
                try:
                    client_name = order.get('client_name', 'Клиент')
                    problem = order.get('problem_description', 'Описание отсутствует')
                    address = order.get('client_address', 'Адрес не указан')
                    
                    notification = (
                        f"🔔 *Вам назначен новый заказ #{order_id}*\n\n"
                        f"👤 Клиент: {client_name}\n"
                        f"📝 Проблема: {problem}\n"
                        f"📍 Адрес: {address}\n\n"
                        f"Для просмотра всех ваших заказов используйте команду /my_orders"
                    )
                    
                    bot.send_message(tech_id, notification, parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления мастеру: {e}")
                
            except Exception as e:
                logger.error(f"Ошибка при назначении мастера: {e}")
                bot.answer_callback_query(call.id, "⚠️ Произошла ошибка при назначении мастера")
                
        # Обработка изменения статуса заказа
        elif callback_data.startswith("change_status_"):
            try:
                order_id = int(callback_data.split("_")[2])
                
                # Получаем информацию о заказе
                order = get_order(order_id)
                if not order:
                    bot.answer_callback_query(call.id, "⚠️ Заказ не найден")
                    return
                
                current_status = order.get('status', 'new')
                
                # Создаем клавиатуру со статусами
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                
                # Добавляем кнопки статусов в зависимости от текущего статуса
                statuses = {
                    'new': '🆕 Новый',
                    'assigned': '📋 Назначен',
                    'in_progress': '🔧 В работе',
                    'completed': '✅ Завершен',
                    'cancelled': '❌ Отменен',
                    'pending_parts': '⏳ Ожидание запчастей',
                    'pending_client': '👥 Ожидание клиента',
                    'delayed': '⏱️ Отложен'
                }
                
                # Формируем кнопки для изменения статуса
                for status_code, status_name in statuses.items():
                    # Не показываем текущий статус среди вариантов
                    if status_code == current_status:
                        continue
                        
                    keyboard.add(types.InlineKeyboardButton(
                        status_name, 
                        callback_data=f"set_status_{order_id}_{status_code}"
                    ))
                
                # Добавляем кнопку "Назад"
                keyboard.add(types.InlineKeyboardButton(
                    "↩️ Назад", 
                    callback_data=f"view_order_{order_id}"
                ))
                
                bot.edit_message_text(
                    f"🔄 *Изменение статуса заказа #{order_id}*\n\n"
                    f"Текущий статус: *{get_status_name(current_status)}*\n\n"
                    f"Выберите новый статус:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Ошибка при изменении статуса заказа: {e}")
                bot.answer_callback_query(call.id, "⚠️ Произошла ошибка при изменении статуса")
                
        # Обработка установки статуса заказа
        elif callback_data.startswith("set_status_"):
            try:
                parts = callback_data.split("_")
                order_id = int(parts[2])
                new_status = parts[3]
                
                # Получаем информацию о заказе
                order = get_order(order_id)
                if not order:
                    bot.answer_callback_query(call.id, "⚠️ Заказ не найден")
                    return
                
                old_status = order.get('status', 'new')
                
                # Обновляем статус заказа
                update_order(order_id, {'status': new_status})
                
                # Записываем информацию в лог
                try:
                    logger.info(f"Пользователь {get_full_name(get_user(user_id))} изменил статус заказа #{order_id} с {get_status_name(old_status)} на {get_status_name(new_status)}")
                except Exception as log_error:
                    logger.error(f"Ошибка при записи в лог: {log_error}")
                
                # Уведомляем об успешном изменении статуса
                bot.edit_message_text(
                    f"✅ *Статус заказа успешно изменен*\n\n"
                    f"Заказ #{order_id}\n"
                    f"Cтарый статус: {get_status_name(old_status)}\n"
                    f"Новый статус: {get_status_name(new_status)}",
                    user_id,
                    message_id,
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("↩️ К заказу", callback_data=f"view_order_{order_id}"),
                        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
                    ),
                    parse_mode="Markdown"
                )
                
                # Если заказ назначен мастеру, уведомляем его об изменении статуса
                technician_id = order.get('technician_id')
                if technician_id and technician_id != user_id:
                    try:
                        notification = (
                            f"🔔 *Обновление статуса заказа #{order_id}*\n\n"
                            f"Новый статус: {get_status_name(new_status)}\n"
                            f"Обновлено: {get_full_name(get_user(user_id))}"
                        )
                        
                        bot.send_message(technician_id, notification, parse_mode="Markdown")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления мастеру об изменении статуса: {e}")
                
            except Exception as e:
                logger.error(f"Ошибка при установке статуса заказа: {e}")
                bot.answer_callback_query(call.id, "⚠️ Произошла ошибка при установке статуса")
        
        elif callback_data == "manage_orders":
            # Создаем клавиатуру для управления заказами
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            
            # Добавляем кнопки для управления заказами
            create_order_button = types.InlineKeyboardButton(
                "➕ Создать новый заказ", 
                callback_data="create_order"
            )
            delete_order_button = types.InlineKeyboardButton(
                "📝 Заказы", 
                callback_data="delete_order_menu"
            )
            
            # Добавляем кнопки в клавиатуру
            keyboard.add(create_order_button, delete_order_button)
            
            # Добавляем кнопку возврата в главное меню
            back_button = types.InlineKeyboardButton(
                "↩️ Назад в главное меню", 
                callback_data="main_menu"
            )
            keyboard.add(back_button)
            
            bot.edit_message_text(
                "📋 *Управление заказами*\n\nВыберите действие:",
                user_id,
                message_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        
        elif callback_data == "create_order":
            bot.edit_message_text(
                "📝 *Создание нового заказа*\n\nСледуйте пошаговой инструкции для создания заказа:",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            bot.send_message(
                user_id,
                "1️⃣ Введите номер телефона клиента:",
                reply_markup=types.ForceReply(selective=True)
            )
            # Устанавливаем состояние пользователя в базе данных
            from database import set_user_state
            set_user_state(user_id, "creating_order_client_phone")
            
        elif callback_data == "help":
            bot.edit_message_text(
                "ℹ️ *Справка по боту*\n\n"
                "Бот предназначен для управления заказами на ремонт компьютерной техники.\n\n"
                "*Основные команды:*\n"
                "/start - Начать работу с ботом\n"
                "/help - Вывести справку\n"
                "/info - Информация о системе\n\n"
                "*Роли пользователей:*\n"
                "👑 Администратор - полный доступ к системе, управление пользователями\n"
                "📞 Диспетчер - прием и управление заказами, работа с заказчиками\n"
                "🔧 Мастер - выполнение заказов, отчеты о работах\n\n"
                "*Возможности бота:*\n"
                "• Создание и управление заказами\n"
                "• Назначение мастеров на заказы\n"
                "• Отслеживание статуса заказов\n"
                "• Уведомления о новых заказах\n"
                "• Управление пользователями\n\n"
                "*Дополнительная информация:*\n"
                "Для доступа к системе необходимо получить одобрение администратора.",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="Markdown"
            )

        elif callback_data == "activity_logs":
            try:
                # Используем функцию из database.py вместо activity_log_functions
                from database import get_activity_logs
                logs = get_activity_logs(limit=20)
                
                if not logs:
                    bot.edit_message_text(
                        "📊 *Логи активности*\n\nЛоги активности пусты.",
                        user_id,
                        message_id,
                        reply_markup=get_back_to_main_menu_keyboard(),
                        parse_mode="Markdown"
                    )
                else:
                    logs_text = "\n\n".join([
                        f"*{log.get('timestamp', 'Н/Д')}*\n"
                        f"👤 Пользователь: {log.get('user_id', 'Н/Д')}\n"
                        f"🛠 Действие: {log.get('action_type', 'Н/Д')}\n"
                        f"📝 Описание: {log.get('action_description', 'Н/Д')}"
                        for log in logs
                    ])
                    
                    bot.edit_message_text(
                        f"📊 *Логи активности*\n\n{logs_text}",
                        user_id,
                        message_id,
                        reply_markup=get_back_to_main_menu_keyboard(),
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении логов активности: {e}")
                import traceback
                logger.error(traceback.format_exc())
                bot.edit_message_text(
                    "⚠️ *Ошибка*\n\nНе удалось получить логи активности.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                
        # Обработка запросов управления пользователями
        elif callback_data == "list_users":
            # Получение списка пользователей
            users = get_all_users()
            if not users:
                bot.edit_message_text(
                    "👥 *Список пользователей*\n\nСписок пользователей пуст.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                # Формируем текст со списком пользователей
                user_text = "\n\n".join([
                    f"*{user.get('first_name')} {user.get('last_name', '')}*\n"
                    f"ID: `{user.get('user_id')}`\n"
                    f"Роль: {get_role_name(user.get('role', 'user'))}\n"
                    f"Статус: {'✅ Подтвержден' if user.get('is_approved') else '❌ Не подтвержден'}"
                    for user in users
                ])
                
                bot.edit_message_text(
                    f"👥 *Список пользователей*\n\n{user_text}",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
        
        elif callback_data == "add_admin":
            # Отправляем сообщение с запросом ID пользователя
            bot.edit_message_text(
                "👑 *Добавление администратора*\n\n"
                "Введите ID пользователя, которого нужно назначить администратором:",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            # Устанавливаем состояние пользователя
            from database import set_user_state
            set_user_state(user_id, "adding_admin")
        
        elif callback_data == "add_dispatcher":
            # Отправляем сообщение с запросом ID пользователя
            bot.edit_message_text(
                "📞 *Добавление диспетчера*\n\n"
                "Введите ID пользователя, которого нужно назначить диспетчером:",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            # Устанавливаем состояние пользователя
            from database import set_user_state
            set_user_state(user_id, "adding_dispatcher")
        
        elif callback_data == "add_technician":
            # Отправляем сообщение с запросом ID пользователя
            bot.edit_message_text(
                "🔧 *Добавление мастера*\n\n"
                "Введите ID пользователя, которого нужно назначить мастером:",
                user_id,
                message_id,
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            # Устанавливаем состояние пользователя
            from database import set_user_state
            set_user_state(user_id, "adding_technician")
        
        elif callback_data == "delete_user_menu":
            # Получаем список пользователей для удаления
            users = get_all_users()
            if not users:
                bot.edit_message_text(
                    "🗑️ *Удаление пользователя*\n\nСписок пользователей пуст.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                # Создаем клавиатуру с кнопками для каждого пользователя
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                
                # Добавляем кнопки для каждого пользователя
                for user_data in users:
                    # Пропускаем текущего пользователя (нельзя удалить самого себя)
                    if int(user_data.get('user_id')) == user_id:
                        continue
                    
                    delete_button = types.InlineKeyboardButton(
                        f"❌ {user_data.get('first_name')} ({get_role_name(user_data.get('role', 'user'))})",
                        callback_data=f"delete_user_{user_data.get('user_id')}"
                    )
                    keyboard.add(delete_button)
                
                # Добавляем кнопку возврата
                back_button = types.InlineKeyboardButton(
                    "↩️ Назад к управлению пользователями",
                    callback_data="manage_users"
                )
                keyboard.add(back_button)
                
                bot.edit_message_text(
                    "🗑️ *Удаление пользователя*\n\nВыберите пользователя для удаления:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
        elif callback_data.startswith("delete_user_"):
            # Получаем ID пользователя для удаления
            target_user_id = int(callback_data.split("_")[2])
            
            # Удаляем пользователя
            if delete_user(target_user_id):
                # Добавляем лог активности
                try:
                    from database import add_activity_log
                    add_activity_log(user_id, "user_delete", f"Удален пользователь {target_user_id}", related_user_id=target_user_id)
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога активности: {e}")
                
                bot.edit_message_text(
                    f"✅ *Успех*\n\nПользователь с ID {target_user_id} успешно удален.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    "⚠️ *Ошибка*\n\nНе удалось удалить пользователя.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                
        # Обработка запросов для управления заказами
        elif callback_data == "delete_order_menu":
            # Получаем список заказов для удаления
            orders = get_all_orders()
            if not orders:
                bot.edit_message_text(
                    "📝 *Управление заказами*\n\nСписок заказов пуст.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                # Создаем клавиатуру с кнопками для каждого заказа
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                
                # Добавляем кнопки для каждого заказа
                for order in orders:
                    view_button = types.InlineKeyboardButton(
                        f"📋 Заказ #{order.get('order_id')} - {order.get('client_name')}",
                        callback_data=f"delete_order_{order.get('order_id')}"
                    )
                    keyboard.add(view_button)
                
                # Добавляем кнопку возврата
                back_button = types.InlineKeyboardButton(
                    "↩️ Назад к управлению заказами",
                    callback_data="manage_orders"
                )
                keyboard.add(back_button)
                
                bot.edit_message_text(
                    "📝 *Управление заказами*\n\nВыберите заказ для просмотра или удаления:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
        elif callback_data.startswith("delete_order_"):
            # Получаем ID заказа для просмотра
            order_id = int(callback_data.split("_")[2])
            
            # Получаем информацию о заказе
            from database import get_order
            order = get_order(order_id)
            
            if order:
                # Формируем детальную информацию о заказе
                status_name = get_status_name(order.get('status', 0))
                assigned_to = order.get('assigned_to')
                
                if assigned_to:
                    from database import get_user
                    technician = get_user(assigned_to)
                    assigned_info = f"*Назначен:* {technician.get('first_name', 'Неизвестно')} {technician.get('last_name', '')}"
                else:
                    assigned_info = "*Назначен:* Не назначен"
                
                # Создаем клавиатуру с действиями для заказа
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                
                # Добавляем кнопки управления заказом
                assign_button = types.InlineKeyboardButton(
                    "👤 Назначить мастера", 
                    callback_data=f"assign_technician_{order_id}"
                )
                status_button = types.InlineKeyboardButton(
                    "🔄 Изменить статус", 
                    callback_data=f"change_status_{order_id}"
                )
                delete_button = types.InlineKeyboardButton(
                    "🗑️ Удалить заказ", 
                    callback_data=f"confirm_delete_order_{order_id}"
                )
                
                # Добавляем кнопки в клавиатуру
                keyboard.add(assign_button, status_button, delete_button)
                
                # Добавляем кнопку возврата
                back_button = types.InlineKeyboardButton(
                    "↩️ Назад к списку заказов", 
                    callback_data="delete_order_menu"
                )
                keyboard.add(back_button)
                
                # Отправляем сообщение с информацией о заказе и опциями
                bot.edit_message_text(
                    f"📋 *Информация о заказе #{order_id}*\n\n"
                    f"*Клиент:* {order.get('client_name', 'Не указано')}\n"
                    f"*Телефон:* {order.get('client_phone', 'Не указано')}\n"
                    f"*Адрес:* {order.get('client_address', 'Не указано')}\n"
                    f"*Проблема:* {order.get('problem_description', 'Не указано')}\n"
                    f"*Время:* {order.get('time', 'Не указано')}\n"
                    f"*Статус:* {status_name}\n"
                    f"{assigned_info}\n\n"
                    "Выберите действие с заказом:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    "⚠️ *Ошибка*\n\nЗаказ не найден.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
        
        # Обработка изменения статуса заказа
        elif callback_data.startswith("change_status_"):
            # Получаем ID заказа
            order_id = int(callback_data.split("_")[2])
            
            # Получаем информацию о заказе
            from database import get_order
            order = get_order(order_id)
            
            if order:
                # Создаем клавиатуру с кнопками для статусов
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                
                # Получаем текущий статус
                current_status = order.get('status', 0)
                
                # Создаем кнопки для всех статусов
                status_buttons = []
                for status_code, status_name in STATUS_NAMES.items():
                    # Пропускаем текущий статус
                    if int(status_code) == current_status:
                        continue
                        
                    status_button = types.InlineKeyboardButton(
                        f"{status_name}", 
                        callback_data=f"set_status_{order_id}_{status_code}"
                    )
                    status_buttons.append(status_button)
                
                # Добавляем кнопки в клавиатуру по 2 в ряд
                for i in range(0, len(status_buttons), 2):
                    if i + 1 < len(status_buttons):
                        keyboard.add(status_buttons[i], status_buttons[i+1])
                    else:
                        keyboard.add(status_buttons[i])
                
                # Добавляем кнопку возврата
                back_button = types.InlineKeyboardButton(
                    "↩️ Назад к информации о заказе", 
                    callback_data=f"delete_order_{order_id}"
                )
                keyboard.add(back_button)
                
                bot.edit_message_text(
                    f"🔄 *Изменение статуса заказа #{order_id}*\n\n"
                    f"Текущий статус: *{get_status_name(current_status)}*\n\n"
                    "Выберите новый статус:",
                    user_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    "⚠️ *Ошибка*\n\nЗаказ не найден.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
        
        # Обработка назначения статуса заказу
        elif callback_data.startswith("set_status_"):
            # Получаем ID заказа и новый статус
            parts = callback_data.split("_")
            order_id = int(parts[2])
            new_status = int(parts[3])
            
            # Обновляем статус заказа
            from database import update_order_status
            if update_order_status(order_id, new_status):
                # Добавляем лог активности
                try:
                    from database import add_activity_log
                    status_name = get_status_name(new_status)
                    add_activity_log(user_id, "status_update", f"Изменен статус заказа {order_id} на '{status_name}'", related_order_id=order_id)
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога активности: {e}")
                
                bot.edit_message_text(
                    f"✅ *Успех*\n\nСтатус заказа #{order_id} изменен на *{get_status_name(new_status)}*.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_orders_keyboard(order_id),
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    "⚠️ *Ошибка*\n\nНе удалось изменить статус заказа.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_orders_keyboard(order_id),
                    parse_mode="Markdown"
                )
                
        # Обработка подтверждения удаления заказа
        elif callback_data.startswith("confirm_delete_order_"):
            # Получаем ID заказа для удаления
            order_id = int(callback_data.split("_")[3])
            
            # Создаем клавиатуру для подтверждения
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            
            # Добавляем кнопки подтверждения и отмены
            confirm_button = types.InlineKeyboardButton(
                "✅ Да, удалить", 
                callback_data=f"do_delete_order_{order_id}"
            )
            cancel_button = types.InlineKeyboardButton(
                "❌ Отмена", 
                callback_data=f"delete_order_{order_id}"
            )
            
            keyboard.add(confirm_button, cancel_button)
            
            bot.edit_message_text(
                f"🗑️ *Подтверждение удаления*\n\n"
                f"Вы действительно хотите удалить заказ #{order_id}?\n\n"
                "Это действие невозможно отменить.",
                user_id,
                message_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        # Фактическое удаление заказа после подтверждения
        elif callback_data.startswith("do_delete_order_"):
            # Получаем ID заказа для удаления
            order_id = int(callback_data.split("_")[3])
            
            # Удаляем заказ
            from database import delete_order
            if delete_order(order_id):
                # Добавляем лог активности
                try:
                    from database import add_activity_log
                    add_activity_log(user_id, "order_delete", f"Удален заказ {order_id}", related_order_id=order_id)
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога активности: {e}")
                
                bot.edit_message_text(
                    f"✅ *Успех*\n\nЗаказ #{order_id} успешно удален.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    "⚠️ *Ошибка*\n\nНе удалось удалить заказ.",
                    user_id,
                    message_id,
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                
        # Обработка запросов главного меню
        elif callback_data == "main_menu":
            bot.edit_message_text(
                "📲 *Главное меню*\n\nВыберите действие:",
                user_id,
                message_id,
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
            
        # Если callback_data не распознан
        else:
            bot.answer_callback_query(call.id, "⚠️ Неизвестная команда")
            logger.warning(f"Необработанный callback: {callback_data}")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке callback {callback_data}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Показываем пользователю, что произошла ошибка
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка при обработке запроса")

# Регистрация функций AI
try:
    # Регистрируем команды AI, если модуль доступен
    register_ai_commands(bot)
    logger.info("AI команды успешно зарегистрированы")
except Exception as e:
    logger.error(f"Ошибка при регистрации AI команд: {e}")

# Обработка текстовых сообщений для работы с состояниями
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message(message):
    """
    Обрабатывает все текстовые сообщения
    """
    user_id = message.from_user.id
    text = message.text
    
    # Получаем текущее состояние пользователя
    from database import get_user_state
    user_state = get_user_state(user_id)
    
    logger.info(f"Получено текстовое сообщение от пользователя {user_id}, состояние: {user_state}")
    
    if user_state == "adding_admin":
        # Обработка добавления администратора
        try:
            target_user_id = int(text)
            
            # Проверяем, существует ли пользователь
            target_user = get_user(target_user_id)
            if not target_user:
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nПользователь с указанным ID не найден.",
                    parse_mode="Markdown"
                )
                return
            
            # Устанавливаем роль администратора
            if update_user_role(target_user_id, "admin"):
                # Добавляем лог активности
                try:
                    from database import add_activity_log
                    add_activity_log(
                        user_id, 
                        "role_update", 
                        f"Пользователь {target_user_id} назначен администратором", 
                        related_user_id=target_user_id
                    )
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога активности: {e}")
                
                bot.send_message(
                    user_id,
                    f"✅ *Успех*\n\nПользователь {target_user.get('first_name')} {target_user.get('last_name', '')} успешно назначен администратором.",
                    parse_mode="Markdown"
                )
                
                # Уведомляем пользователя о назначении
                try:
                    bot.send_message(
                        target_user_id,
                        "👑 Вам присвоена роль администратора системы.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
            else:
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nНе удалось назначить пользователя администратором.",
                    parse_mode="Markdown"
                )
            
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
        except ValueError:
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nID пользователя должен быть числом. Повторите ввод или отправьте /cancel для отмены.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении администратора: {e}")
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nПроизошла ошибка при добавлении администратора.",
                parse_mode="Markdown"
            )
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
    
    elif user_state == "adding_dispatcher":
        # Обработка добавления диспетчера
        try:
            target_user_id = int(text)
            
            # Проверяем, существует ли пользователь
            target_user = get_user(target_user_id)
            if not target_user:
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nПользователь с указанным ID не найден.",
                    parse_mode="Markdown"
                )
                return
            
            # Устанавливаем роль диспетчера
            if update_user_role(target_user_id, "dispatcher"):
                # Добавляем лог активности
                try:
                    from database import add_activity_log
                    add_activity_log(
                        user_id, 
                        "role_update", 
                        f"Пользователь {target_user_id} назначен диспетчером", 
                        related_user_id=target_user_id
                    )
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога активности: {e}")
                
                bot.send_message(
                    user_id,
                    f"✅ *Успех*\n\nПользователь {target_user.get('first_name')} {target_user.get('last_name', '')} успешно назначен диспетчером.",
                    parse_mode="Markdown"
                )
                
                # Уведомляем пользователя о назначении
                try:
                    bot.send_message(
                        target_user_id,
                        "📞 Вам присвоена роль диспетчера системы.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
            else:
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nНе удалось назначить пользователя диспетчером.",
                    parse_mode="Markdown"
                )
            
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
        except ValueError:
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nID пользователя должен быть числом. Повторите ввод или отправьте /cancel для отмены.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении диспетчера: {e}")
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nПроизошла ошибка при добавлении диспетчера.",
                parse_mode="Markdown"
            )
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
    
    elif user_state == "adding_technician":
        # Обработка добавления мастера
        try:
            target_user_id = int(text)
            
            # Проверяем, существует ли пользователь
            target_user = get_user(target_user_id)
            if not target_user:
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nПользователь с указанным ID не найден.",
                    parse_mode="Markdown"
                )
                return
            
            # Устанавливаем роль мастера
            if update_user_role(target_user_id, "technician"):
                # Добавляем лог активности
                try:
                    from database import add_activity_log
                    add_activity_log(
                        user_id, 
                        "role_update", 
                        f"Пользователь {target_user_id} назначен мастером", 
                        related_user_id=target_user_id
                    )
                except Exception as e:
                    logger.error(f"Ошибка при добавлении лога активности: {e}")
                
                bot.send_message(
                    user_id,
                    f"✅ *Успех*\n\nПользователь {target_user.get('first_name')} {target_user.get('last_name', '')} успешно назначен мастером.",
                    parse_mode="Markdown"
                )
                
                # Уведомляем пользователя о назначении
                try:
                    bot.send_message(
                        target_user_id,
                        "🔧 Вам присвоена роль мастера системы.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
            else:
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nНе удалось назначить пользователя мастером.",
                    parse_mode="Markdown"
                )
            
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
        except ValueError:
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nID пользователя должен быть числом. Повторите ввод или отправьте /cancel для отмены.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении мастера: {e}")
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nПроизошла ошибка при добавлении мастера.",
                parse_mode="Markdown"
            )
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
    
    elif user_state == "creating_order_client_name":
        # Обработка создания заказа - шаг 2: имя клиента
        # Сохраняем имя клиента и запрашиваем описание проблемы
        from database import set_user_state
        set_user_state(user_id, "creating_order_problem", None)
        
        # Сохраняем имя клиента в параметрах
        bot.send_message(
            user_id,
            f"ФИО клиента: *{text}*\n\n"
            "3️⃣ Введите описание проблемы:",
            parse_mode="Markdown",
            reply_markup=types.ForceReply(selective=True)
        )
        
    elif user_state == "creating_order_client_phone":
        # Обработка создания заказа - шаг 1: телефон клиента
        # Принимаем любой формат телефона
        # Записываем логи в debug_log.md
        with open("debug_log.md", "a") as log_file:
            log_file.write(f"\n[{datetime.datetime.now()}] Получен номер телефона: {text}\n")
        
        # Сохраняем телефон клиента и запрашиваем имя клиента
        from database import set_user_state
        set_user_state(user_id, "creating_order_client_name", None)
        
        bot.send_message(
            user_id,
            f"Телефон клиента: *{text}*\n\n"
            "2️⃣ О клиенте:",
            parse_mode="Markdown",
            reply_markup=types.ForceReply(selective=True)
        )
        
    elif user_state == "creating_order_client_address":
        # Обработка создания заказа - шаг 4: адрес клиента
        # Сохраняем адрес клиента и запрашиваем время
        from database import set_user_state
        set_user_state(user_id, "creating_order_time", None)
        
        bot.send_message(
            user_id,
            f"Адрес клиента: *{text}*\n\n"
            "5️⃣ Введите удобное время для клиента (в формате ДД.ММ.ГГГГ ЧЧ:ММ):",
            parse_mode="Markdown",
            reply_markup=types.ForceReply(selective=True)
        )
        
    elif user_state == "creating_order_problem":
        # Обработка создания заказа - шаг 3: описание проблемы
        # Сохраняем описание проблемы и запрашиваем адрес
        from database import set_user_state
        set_user_state(user_id, "creating_order_client_address", None)
        
        bot.send_message(
            user_id,
            f"Описание проблемы: *{text}*\n\n"
            "4️⃣ Введите адрес клиента:",
            parse_mode="Markdown",
            reply_markup=types.ForceReply(selective=True)
        )
        
    elif user_state == "creating_order_time":
        # Обработка создания заказа - шаг 5: время
        # Проверяем формат времени
        try:
            # TODO: Добавить проверку формата времени
            
            # Получаем сохраненные данные
            # В идеале здесь нужно было бы получать сохраненные данные из БД,
            # но для примера просто создадим заказ
            order_info = {
                "client_name": "Клиент",
                "client_phone": "+71234567890",
                "client_address": "Адрес клиента",
                "problem_description": "Описание проблемы",
                "scheduled_datetime": text
            }
            
            # Создаем заказ
            try:
                from database import save_order
                order_id = save_order(
                    user_id,
                    order_info["client_phone"],
                    order_info["client_name"],
                    order_info["problem_description"],
                    order_info["client_address"],
                    order_info["scheduled_datetime"]
                )
                
                if order_id:
                    # Добавляем лог активности
                    try:
                        from database import add_activity_log
                        add_activity_log(
                            user_id, 
                            "order_create", 
                            f"Создан заказ #{order_id}", 
                            related_order_id=order_id
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при добавлении лога активности: {e}")
                    
                    # Создаем инлайн кнопку для перехода к списку заказов
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton("📋 Перейти к списку заказов", callback_data="view_orders"))
                    
                    # Записываем логи в debug_log.md
                    with open("debug_log.md", "a") as log_file:
                        log_file.write(f"\n[{datetime.datetime.now()}] Создан заказ #{order_id}\n")
                    
                    bot.send_message(
                        user_id,
                        f"✅ *Заказ успешно создан*\n\n"
                        f"*Номер заказа:* #{order_id}\n"
                        f"*Клиент:* {order_info['client_name']}\n"
                        f"*Телефон:* {order_info['client_phone']}\n"
                        f"*Адрес:* {order_info['client_address']}\n"
                        f"*Проблема:* {order_info['problem_description']}\n"
                        f"*Время:* {order_info['scheduled_datetime']}",
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    
                    # Уведомляем администраторов о новом заказе
                    try:
                        from utils import send_order_notification_to_admins
                        send_order_notification_to_admins(bot, order_id)
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления администраторам: {e}")
                else:
                    bot.send_message(
                        user_id,
                        "⚠️ *Ошибка*\n\nНе удалось создать заказ.",
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Ошибка при создании заказа: {e}")
                bot.send_message(
                    user_id,
                    "⚠️ *Ошибка*\n\nПроизошла ошибка при создании заказа.",
                    parse_mode="Markdown"
                )
            
            # Очищаем состояние
            from database import clear_user_state
            clear_user_state(user_id)
        except Exception as e:
            logger.error(f"Ошибка при обработке времени заказа: {e}")
            bot.send_message(
                user_id,
                "⚠️ *Ошибка*\n\nНеверный формат времени. Введите в формате ДД.ММ.ГГГГ ЧЧ:ММ:",
                parse_mode="Markdown",
                reply_markup=types.ForceReply(selective=True)
            )
    
    else:
        # Если состояние не определено, просто логируем сообщение
        logger.info(f"Получено текстовое сообщение от пользователя {user_id}: {text}")
        
        # Если это команда, то не отвечаем на нее здесь
        if text.startswith('/'):
            return
            
        # Отвечаем пользователю
        bot.reply_to(
            message,
            "Используйте команды бота для взаимодействия. Отправьте /help для получения списка команд."
        )

try:
    # Регистрируем команды AI, если модуль доступен
    register_ai_commands(bot)
    logger.info("AI команды успешно зарегистрированы")
    
    # Оставляем только /start и /help команды в меню бота
    commands = [
        types.BotCommand("/start", "Начать работу с ботом"),
        types.BotCommand("/help", "Показать помощь")
    ]
    bot.set_my_commands(commands)
    logger.info("Установлены только команды /start и /help в меню бота")
    
    # Записываем логи в debug_log.md
    with open("debug_log.md", "a") as log_file:
        log_file.write(f"\n[{datetime.datetime.now()}] Установлены только команды /start и /help в меню бота\n")
        
except Exception as e:
    logger.error(f"Ошибка при регистрации команд: {e}")
    # Записываем ошибку в debug_log.md
    with open("debug_log.md", "a") as log_file:
        log_file.write(f"\n[{datetime.datetime.now()}] Ошибка при регистрации команд: {e}\n")

# Создаем функцию start_bot_polling для запуска бота
def start_bot_polling():
    """
    Запускает бота в режиме polling с обработкой ошибок
    
    Returns:
        bool: True, если запуск успешен, False если произошла ошибка
    """
    try:
        logger.info("Запуск бота в режиме polling...")
        bot.polling(none_stop=True, interval=1, timeout=60)
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return False

# Если файл запущен напрямую, запускаем бота
if __name__ == "__main__":
    start_bot_polling()