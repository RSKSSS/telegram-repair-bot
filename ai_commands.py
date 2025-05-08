"""
Модуль с командами Telegram бота для взаимодействия с ИИ функциями
"""

import json
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from shared_state import clear_user_state, set_user_state, get_user_state, get_current_order_id, bot
from database import get_user_role, get_order, get_activity_logs, update_order, add_activity_log
from logger import get_component_logger
from ui_constants import EMOJI, format_success_message, format_error_message
from ai_assistant import (
    analyze_problem_description, 
    suggest_service_cost, 
    generate_service_description,
    summarize_order_history,
    answer_customer_question,
    assist_technician
)

# Настройка логирования
logger = get_component_logger('ai_commands')

# Состояния для обработки ИИ-функций
AI_STATES = {
    'waiting_for_problem_analysis': 'Ожидание описания проблемы для анализа',
    'waiting_for_cost_suggestion': 'Ожидание информации для предложения стоимости',
    'waiting_for_description_generation': 'Ожидание информации для генерации описания работ',
    'waiting_for_technician_question': 'Ожидание вопроса для помощи мастеру',
    'waiting_for_customer_question': 'Ожидание вопроса клиента',
}

# Команды
def register_ai_commands(bot_instance):
    """
    Регистрирует команды для работы с ИИ функциями
    """
    bot_instance.register_message_handler(handle_analyze_problem_command, commands=['analyze_problem'])
    bot_instance.register_message_handler(handle_suggest_cost_command, commands=['suggest_cost'])
    bot_instance.register_message_handler(handle_generate_description_command, commands=['generate_description'])
    bot_instance.register_message_handler(handle_ai_help_command, commands=['ai_help'])
    bot_instance.register_message_handler(handle_technician_help_command, commands=['technician_help'])
    bot_instance.register_message_handler(handle_answer_customer_command, commands=['answer_customer'])

def get_ai_help_menu_keyboard():
    """
    Возвращает клавиатуру с доступными ИИ функциями
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['description']} Анализ проблемы", callback_data="ai_analyze_problem"),
        InlineKeyboardButton(f"{EMOJI['cost']} Предложить стоимость", callback_data="ai_suggest_cost")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['edit']} Генерировать описание", callback_data="ai_generate_description"),
        InlineKeyboardButton(f"{EMOJI['help']} Помощь мастеру", callback_data="ai_technician_help")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['back']} Назад в главное меню", callback_data="main_menu")
    )
    return keyboard

def handle_ai_help_command(message: Message):
    """
    Обработчик команды /ai_help
    Показывает меню с доступными ИИ функциями
    """
    user_id = message.from_user.id
    user_role = get_user_role(user_id)
    
    # Проверяем права доступа
    if not user_role:
        bot.send_message(user_id, "Вы должны быть зарегистрированы для использования этой функции.")
        return
    
    # Отправляем меню с ИИ функциями
    bot.send_message(
        user_id,
        f"{EMOJI['info']} *Доступные ИИ функции:*\n\n"
        f"Выберите функцию из меню ниже или используйте соответствующую команду:\n"
        f"`/analyze_problem` - Анализ описания проблемы\n"
        f"`/suggest_cost` - Предложение стоимости услуг\n"
        f"`/generate_description` - Генерация описания выполненных работ\n"
        f"`/technician_help` - Помощь мастеру в решении проблемы\n"
        f"`/answer_customer` - Помощь в ответе на вопрос клиента\n",
        parse_mode="Markdown",
        reply_markup=get_ai_help_menu_keyboard()
    )

def handle_analyze_problem_command(message: Message):
    """
    Обработчик команды /analyze_problem
    Запрашивает описание проблемы для анализа с помощью ИИ
    """
    user_id = message.from_user.id
    user_role = get_user_role(user_id)
    
    # Проверяем права доступа (может использовать любой зарегистрированный пользователь)
    if not user_role:
        bot.send_message(user_id, "Вы должны быть зарегистрированы для использования этой функции.")
        return
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_problem_analysis'])
    
    # Отправляем инструкции
    bot.send_message(
        user_id,
        f"{EMOJI['info']} Введите описание проблемы для анализа.\n\n"
        f"Я проанализирую описание и предоставлю рекомендации по:\n"
        f"• Категории проблемы\n"
        f"• Сложности и серьезности\n"
        f"• Оценке времени на решение\n"
        f"• Возможным решениям\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )

def handle_suggest_cost_command(message: Message):
    """
    Обработчик команды /suggest_cost
    Запрашивает описание проблемы и выполненных работ для предложения стоимости
    """
    user_id = message.from_user.id
    user_role = get_user_role(user_id)
    
    # Проверяем права доступа (может использовать диспетчер, мастер или админ)
    if not user_role or user_role not in ['admin', 'dispatcher', 'technician']:
        bot.send_message(user_id, "У вас нет прав для использования этой функции.")
        return
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_cost_suggestion'])
    
    # Отправляем инструкции
    bot.send_message(
        user_id,
        f"{EMOJI['info']} Введите описание проблемы и выполненных работ для предложения стоимости.\n\n"
        f"Формат:\n"
        f"Проблема: [описание проблемы]\n"
        f"Выполненные работы: [описание работ]\n\n"
        f"Я проанализирую информацию и предложу диапазон стоимости услуг.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )

def handle_generate_description_command(message: Message):
    """
    Обработчик команды /generate_description
    Запрашивает описание проблемы и выполненных действий для генерации профессионального отчета
    """
    user_id = message.from_user.id
    user_role = get_user_role(user_id)
    
    # Проверяем права доступа (может использовать только мастер или админ)
    if not user_role or user_role not in ['admin', 'technician']:
        bot.send_message(user_id, "У вас нет прав для использования этой функции.")
        return
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_description_generation'])
    
    # Отправляем инструкции
    bot.send_message(
        user_id,
        f"{EMOJI['info']} Введите описание проблемы и список выполненных действий.\n\n"
        f"Формат: \n"
        f"Проблема: [описание проблемы]\n"
        f"Действия: \n"
        f"- [действие 1]\n"
        f"- [действие 2]\n"
        f"...\n\n"
        f"Я сгенерирую профессиональное описание выполненных работ.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )

def handle_technician_help_command(message: Message):
    """
    Обработчик команды /technician_help
    Запрашивает описание проблемы для помощи мастеру
    """
    user_id = message.from_user.id
    user_role = get_user_role(user_id)
    
    # Проверяем права доступа (может использовать мастер или админ)
    if not user_role or user_role not in ['admin', 'technician']:
        bot.send_message(user_id, "У вас нет прав для использования этой функции.")
        return
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_technician_question'])
    
    # Отправляем инструкции
    bot.send_message(
        user_id,
        f"{EMOJI['info']} Опишите проблему, с которой вы столкнулись, или задайте вопрос.\n\n"
        f"Я предоставлю рекомендации по диагностике и решению проблемы.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )

def handle_answer_customer_command(message: Message):
    """
    Обработчик команды /answer_customer
    Запрашивает вопрос клиента для генерации ответа
    """
    user_id = message.from_user.id
    user_role = get_user_role(user_id)
    
    # Проверяем права доступа (может использовать диспетчер или админ)
    if not user_role or user_role not in ['admin', 'dispatcher']:
        bot.send_message(user_id, "У вас нет прав для использования этой функции.")
        return
    
    # Проверяем, есть ли текущий заказ
    order_id = get_current_order_id(user_id)
    if not order_id:
        bot.send_message(
            user_id,
            format_error_message("Сначала выберите заказ, используя команду /my_orders или соответствующую кнопку в меню."),
            parse_mode="Markdown"
        )
        return
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_customer_question'])
    
    # Отправляем инструкции
    bot.send_message(
        user_id,
        f"{EMOJI['info']} Введите вопрос клиента, на который вы хотите получить ответ.\n\n"
        f"Я сгенерирую вежливый и информативный ответ на основе данных о заказе #{order_id}.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )

def handle_cancel_command(message: Message):
    """
    Обработчик команды /cancel
    Отменяет текущую ИИ операцию
    """
    user_id = message.from_user.id
    
    # Очищаем состояние пользователя
    clear_user_state(user_id)
    
    # Отправляем уведомление об отмене
    bot.send_message(
        user_id,
        format_success_message("Операция отменена"),
        parse_mode="Markdown"
    )

# Обработчики состояний
def handle_problem_analysis_input(user_id: int, text: str):
    """
    Обрабатывает ввод описания проблемы для анализа
    """
    try:
        # Анализируем проблему с помощью ИИ
        result = analyze_problem_description(text)
        
        # Формируем сообщение с результатами
        message = f"{EMOJI['info']} *Анализ проблемы:*\n\n"
        
        # Категория проблемы
        category_mapping = {
            'hardware': 'Аппаратная проблема',
            'software': 'Программная проблема',
            'network': 'Сетевая проблема',
            'peripheral': 'Проблема с периферией',
            'other': 'Другая проблема'
        }
        category = category_mapping.get(result.get('category', 'other'), 'Другая проблема')
        message += f"*Категория:* {category}\n"
        
        # Серьезность проблемы
        severity = result.get('severity', 3)
        severity_emojis = {1: '🟢', 2: '🟢', 3: '🟡', 4: '🟠', 5: '🔴'}
        severity_emoji = severity_emojis.get(severity, '⚪')
        message += f"*Серьезность:* {severity_emoji} {severity}/5\n"
        
        # Оценка времени
        est_time = result.get('estimated_time', 'не определено')
        message += f"*Примерное время решения:* {est_time} ч.\n\n"
        
        # Необходимые запчасти
        parts = result.get('required_parts', [])
        if parts:
            message += f"*Необходимые запчасти:*\n"
            for part in parts:
                message += f"• {part}\n"
            message += "\n"
        
        # Возможные решения
        solutions = result.get('possible_solutions', [])
        if solutions:
            message += f"*Возможные решения:*\n"
            for i, solution in enumerate(solutions, 1):
                message += f"{i}. {solution}\n"
            message += "\n"
        
        # Дополнительные вопросы
        questions = result.get('questions', [])
        if questions:
            message += f"*Рекомендуемые уточняющие вопросы:*\n"
            for i, question in enumerate(questions, 1):
                message += f"{i}. {question}\n"
        
        # Отправляем результат
        bot.send_message(user_id, message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при анализе проблемы: {e}")
        bot.send_message(
            user_id,
            format_error_message(f"Произошла ошибка при анализе проблемы: {str(e)}"),
            parse_mode="Markdown"
        )
    finally:
        # Очищаем состояние пользователя
        clear_user_state(user_id)

def handle_cost_suggestion_input(user_id: int, text: str):
    """
    Обрабатывает ввод для предложения стоимости услуг
    """
    try:
        # Разбираем ввод пользователя
        problem_desc = ""
        service_desc = None
        
        if "Проблема:" in text and "Выполненные работы:" in text:
            parts = text.split("Выполненные работы:")
            problem_desc = parts[0].replace("Проблема:", "").strip()
            service_desc = parts[1].strip()
        else:
            problem_desc = text
        
        # Получаем предложение по стоимости услуг
        result = suggest_service_cost(problem_desc, service_desc)
        
        # Формируем сообщение с результатами
        message = f"{EMOJI['cost']} *Предложение по стоимости услуг:*\n\n"
        
        # Рекомендуемая стоимость
        min_cost = result.get('min_cost', 0)
        max_cost = result.get('max_cost', 0)
        rec_cost = result.get('recommended_cost', 0)
        
        message += f"*Рекомендуемая стоимость:* {rec_cost} руб.\n"
        message += f"*Диапазон стоимости:* {min_cost} - {max_cost} руб.\n"
        
        # Сложность работ
        complexity = result.get('complexity', 3)
        complexity_emojis = {1: '🟢', 2: '🟢', 3: '🟡', 4: '🟠', 5: '🔴'}
        complexity_emoji = complexity_emojis.get(complexity, '⚪')
        message += f"*Сложность работ:* {complexity_emoji} {complexity}/5\n\n"
        
        # Обоснование стоимости
        justification = result.get('justification', '')
        if justification:
            message += f"*Обоснование:*\n{justification}\n"
        
        # Отправляем результат
        bot.send_message(user_id, message, parse_mode="Markdown")
        
        # Если пользователь работает с заказом, предлагаем обновить стоимость
        order_id = get_current_order_id(user_id)
        if order_id:
            # Создаем клавиатуру для обновления стоимости
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    f"Установить стоимость {rec_cost} руб.", 
                    callback_data=f"set_cost_{order_id}_{rec_cost}"
                )
            )
            
            bot.send_message(
                user_id,
                f"Хотите установить рекомендуемую стоимость {rec_cost} руб. для заказа #{order_id}?",
                reply_markup=keyboard
            )
        
    except Exception as e:
        logger.error(f"Ошибка при предложении стоимости: {e}")
        bot.send_message(
            user_id,
            format_error_message(f"Произошла ошибка при предложении стоимости: {str(e)}"),
            parse_mode="Markdown"
        )
    finally:
        # Очищаем состояние пользователя
        clear_user_state(user_id)

def handle_description_generation_input(user_id: int, text: str):
    """
    Обрабатывает ввод для генерации описания выполненных работ
    """
    try:
        # Разбираем ввод пользователя
        problem_desc = ""
        actions = []
        
        if "Проблема:" in text and "Действия:" in text:
            parts = text.split("Действия:")
            problem_desc = parts[0].replace("Проблема:", "").strip()
            
            actions_text = parts[1].strip()
            # Извлекаем действия из списка с тире или звездочками
            action_lines = actions_text.split("\n")
            for line in action_lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                    actions.append(line[1:].strip())
        else:
            problem_desc = text
        
        # Если действия не удалось извлечь из форматированного списка,
        # используем весь текст как описание проблемы
        if not actions:
            problem_desc = text
            actions = ["Диагностика проблемы", "Применение соответствующих мер для решения"]
        
        # Генерируем описание выполненных работ
        result = generate_service_description(problem_desc, actions)
        
        # Отправляем результат
        message = f"{EMOJI['description']} *Сгенерированное описание выполненных работ:*\n\n{result}"
        
        bot.send_message(user_id, message, parse_mode="Markdown")
        
        # Если пользователь работает с заказом, предлагаем обновить описание
        order_id = get_current_order_id(user_id)
        if order_id:
            # Создаем клавиатуру для обновления описания
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    f"Установить это описание для заказа #{order_id}", 
                    callback_data=f"set_description_{order_id}"
                )
            )
            
            # Сохраняем описание во временные данные пользователя
            bot.user_data[user_id] = {"generated_description": result}
            
            bot.send_message(
                user_id,
                f"Хотите установить это описание для заказа #{order_id}?",
                reply_markup=keyboard
            )
        
    except Exception as e:
        logger.error(f"Ошибка при генерации описания: {e}")
        bot.send_message(
            user_id,
            format_error_message(f"Произошла ошибка при генерации описания: {str(e)}"),
            parse_mode="Markdown"
        )
    finally:
        # Очищаем состояние пользователя
        clear_user_state(user_id)

def handle_technician_question_input(user_id: int, text: str):
    """
    Обрабатывает ввод вопроса мастера
    """
    try:
        # Получаем рекомендации для мастера
        result = assist_technician(text)
        
        # Формируем сообщение с результатами
        message = f"{EMOJI['info']} *Рекомендации по решению проблемы:*\n\n"
        
        # Шаги диагностики
        diagnostic_steps = result.get('diagnostic_steps', [])
        if diagnostic_steps:
            message += f"*Шаги диагностики:*\n"
            for i, step in enumerate(diagnostic_steps, 1):
                message += f"{i}. {step}\n"
            message += "\n"
        
        # Возможные причины
        causes = result.get('possible_causes', [])
        if causes:
            message += f"*Возможные причины:*\n"
            for i, cause in enumerate(causes, 1):
                message += f"{i}. {cause}\n"
            message += "\n"
        
        # Шаги для решения
        solution_steps = result.get('solution_steps', [])
        if solution_steps:
            message += f"*Рекомендуемые действия:*\n"
            for i, step in enumerate(solution_steps, 1):
                message += f"{i}. {step}\n"
            message += "\n"
        
        # Необходимые инструменты
        tools = result.get('required_tools', [])
        if tools:
            message += f"*Необходимые инструменты:*\n"
            for tool in tools:
                message += f"• {tool}\n"
            message += "\n"
        
        # Меры предосторожности
        precautions = result.get('precautions', [])
        if precautions:
            message += f"*Меры предосторожности:*\n"
            for precaution in precautions:
                message += f"⚠️ {precaution}\n"
            message += "\n"
        
        # Дополнительные ресурсы
        resources = result.get('additional_resources', [])
        if resources:
            message += f"*Полезные ресурсы:*\n"
            for resource in resources:
                message += f"🔗 {resource}\n"
        
        # Отправляем результат
        bot.send_message(user_id, message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса мастера: {e}")
        bot.send_message(
            user_id,
            format_error_message(f"Произошла ошибка при обработке вопроса: {str(e)}"),
            parse_mode="Markdown"
        )
    finally:
        # Очищаем состояние пользователя
        clear_user_state(user_id)

def handle_customer_question_input(user_id: int, text: str):
    """
    Обрабатывает ввод вопроса клиента для генерации ответа
    """
    try:
        # Получаем ID текущего заказа
        order_id = get_current_order_id(user_id)
        if not order_id:
            bot.send_message(
                user_id,
                format_error_message("Не найден активный заказ. Пожалуйста, выберите заказ через /my_orders."),
                parse_mode="Markdown"
            )
            clear_user_state(user_id)
            return
        
        # Получаем информацию о заказе
        order = get_order(order_id)
        if not order:
            bot.send_message(
                user_id,
                format_error_message(f"Не удалось получить информацию о заказе #{order_id}."),
                parse_mode="Markdown"
            )
            clear_user_state(user_id)
            return
        
        # Получаем ответ на вопрос клиента
        answer = answer_customer_question(text, order)
        
        # Отправляем результат
        message = f"{EMOJI['info']} *Ответ на вопрос клиента:*\n\n{answer}"
        
        bot.send_message(user_id, message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа клиенту: {e}")
        bot.send_message(
            user_id,
            format_error_message(f"Произошла ошибка при генерации ответа: {str(e)}"),
            parse_mode="Markdown"
        )
    finally:
        # Очищаем состояние пользователя
        clear_user_state(user_id)

# Обработчики callback-запросов для ИИ функций
def handle_ai_analyze_problem_callback(user_id: int, message_id: int):
    """
    Обработчик callback-запроса ai_analyze_problem
    """
    # Редактируем сообщение и запрашиваем ввод описания проблемы
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"{EMOJI['info']} Введите описание проблемы для анализа.\n\n"
        f"Я проанализирую описание и предоставлю рекомендации по:\n"
        f"• Категории проблемы\n"
        f"• Сложности и серьезности\n"
        f"• Оценке времени на решение\n"
        f"• Возможным решениям\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_problem_analysis'])

def handle_ai_suggest_cost_callback(user_id: int, message_id: int):
    """
    Обработчик callback-запроса ai_suggest_cost
    """
    # Редактируем сообщение и запрашиваем ввод описания проблемы
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"{EMOJI['info']} Введите описание проблемы и выполненных работ для предложения стоимости.\n\n"
        f"Формат: \n"
        f"Проблема: [описание проблемы]\n"
        f"Выполненные работы: [описание работ]\n\n"
        f"Я проанализирую информацию и предложу диапазон стоимости услуг.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_cost_suggestion'])

def handle_ai_generate_description_callback(user_id: int, message_id: int):
    """
    Обработчик callback-запроса ai_generate_description
    """
    # Редактируем сообщение и запрашиваем ввод описания проблемы и действий
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"{EMOJI['info']} Введите описание проблемы и список выполненных действий.\n\n"
        f"Формат: \n"
        f"Проблема: [описание проблемы]\n"
        f"Действия: \n"
        f"- [действие 1]\n"
        f"- [действие 2]\n"
        f"...\n\n"
        f"Я сгенерирую профессиональное описание выполненных работ.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_description_generation'])

def handle_ai_technician_help_callback(user_id: int, message_id: int):
    """
    Обработчик callback-запроса ai_technician_help
    """
    # Редактируем сообщение и запрашиваем ввод вопроса
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f"{EMOJI['info']} Опишите проблему, с которой вы столкнулись, или задайте вопрос.\n\n"
        f"Я предоставлю рекомендации по диагностике и решению проблемы.\n\n"
        f"Чтобы отменить, отправьте /cancel",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние пользователя
    set_user_state(user_id, AI_STATES['waiting_for_technician_question'])

def handle_set_cost_callback(user_id: int, message_id: int, order_id: int, cost: float):
    """
    Обработчик callback-запроса set_cost_{order_id}_{cost}
    """
    try:
        # Получаем информацию о заказе
        order = get_order(order_id)
        if not order:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_error_message(f"Не удалось получить информацию о заказе #{order_id}."),
                parse_mode="Markdown"
            )
            return
        
        # Обновляем стоимость услуг
        if update_order(order_id, service_cost=cost):
            # Добавляем запись в лог активности
            add_activity_log(
                user_id,
                'cost_update',
                f"Обновлена стоимость заказа #{order_id} до {cost} руб. (с помощью ИИ)",
                related_order_id=order_id
            )
            
            # Отправляем уведомление об успешном обновлении
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_success_message(f"Стоимость услуг для заказа #{order_id} успешно обновлена до {cost} руб."),
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_error_message(f"Не удалось обновить стоимость заказа #{order_id}."),
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении стоимости: {e}")
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=format_error_message(f"Произошла ошибка при обновлении стоимости: {str(e)}"),
            parse_mode="Markdown"
        )

def handle_set_description_callback(user_id: int, message_id: int, order_id: int):
    """
    Обработчик callback-запроса set_description_{order_id}
    """
    try:
        # Получаем сгенерированное описание из временных данных
        if user_id not in bot.user_data or "generated_description" not in bot.user_data[user_id]:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_error_message("Сгенерированное описание не найдено. Пожалуйста, повторите генерацию."),
                parse_mode="Markdown"
            )
            return
        
        description = bot.user_data[user_id]["generated_description"]
        
        # Получаем информацию о заказе
        order = get_order(order_id)
        if not order:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_error_message(f"Не удалось получить информацию о заказе #{order_id}."),
                parse_mode="Markdown"
            )
            return
        
        # Обновляем описание выполненных работ
        if update_order(order_id, service_description=description):
            # Добавляем запись в лог активности
            add_activity_log(
                user_id,
                'description_update',
                f"Обновлено описание работ для заказа #{order_id} (с помощью ИИ)",
                related_order_id=order_id
            )
            
            # Отправляем уведомление об успешном обновлении
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_success_message(f"Описание выполненных работ для заказа #{order_id} успешно обновлено."),
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=format_error_message(f"Не удалось обновить описание работ для заказа #{order_id}."),
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении описания: {e}")
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=format_error_message(f"Произошла ошибка при обновлении описания: {str(e)}"),
            parse_mode="Markdown"
        )

# Обработчик всех текстовых сообщений для ИИ функций
def handle_ai_message_input(message: Message):
    """
    Обрабатывает текстовые сообщения для ИИ функций
    """
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем, если это команда /cancel
    if text == '/cancel':
        handle_cancel_command(message)
        return True  # Сообщение обработано
    
    # Получаем текущее состояние пользователя
    state = get_user_state(user_id)
    
    # Проверяем, находится ли пользователь в одном из ИИ состояний
    if state == AI_STATES['waiting_for_problem_analysis']:
        handle_problem_analysis_input(user_id, text)
        return True  # Сообщение обработано
    
    elif state == AI_STATES['waiting_for_cost_suggestion']:
        handle_cost_suggestion_input(user_id, text)
        return True  # Сообщение обработано
    
    elif state == AI_STATES['waiting_for_description_generation']:
        handle_description_generation_input(user_id, text)
        return True  # Сообщение обработано
    
    elif state == AI_STATES['waiting_for_technician_question']:
        handle_technician_question_input(user_id, text)
        return True  # Сообщение обработано
    
    elif state == AI_STATES['waiting_for_customer_question']:
        handle_customer_question_input(user_id, text)
        return True  # Сообщение обработано
    
    # Сообщение не обработано (не связано с ИИ функциями)
    return False