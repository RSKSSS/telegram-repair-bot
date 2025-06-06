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
    logger.info("Регистрация AI команд с использованием декораторов...")
    # Ничего не делаем здесь, так как обработчики уже оформлены как декораторы ниже
    pass

# Регистрируем команды через декораторы
@bot.message_handler(commands=['analyze_problem'])
def handle_analyze_problem_command(message: Message):
    """
    Обработчик команды /analyze_problem
    Запрашивает описание проблемы для анализа с помощью ИИ
    """
    user_id = message.from_user.id
    
    # Проверяем роль пользователя - должен быть диспетчером или админом
    role = get_user_role(user_id)
    if role not in ['admin', 'dispatcher']:
        bot.reply_to(message, format_error_message("Эта команда доступна только для диспетчеров и админов."))
        return
    
    # Запрашиваем информацию для анализа
    bot.reply_to(
        message,
        f"{EMOJI['ai']} *Анализ проблемы клиента*\n\n"
        "Опишите проблему клиента, и я помогу вам проанализировать её, "
        "предложить возможные причины и решения.\n\n"
        "Пример: _Компьютер перезагружается каждые 15-20 минут, особенно при запуске игр. "
        "При этом слышны странные звуки из системного блока._\n\n"
        "Напишите /cancel для отмены.",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние ожидания ввода описания проблемы
    set_user_state(user_id, 'waiting_for_problem_analysis')

@bot.message_handler(commands=['suggest_cost'])
def handle_suggest_cost_command(message: Message):
    """
    Обработчик команды /suggest_cost
    Запрашивает описание проблемы и выполненных работ для предложения стоимости
    """
    user_id = message.from_user.id
    
    # Проверяем роль пользователя - должен быть диспетчером, техником или админом
    role = get_user_role(user_id)
    if role not in ['admin', 'dispatcher', 'technician']:
        bot.reply_to(message, format_error_message("Эта команда доступна только для диспетчеров, мастеров и админов."))
        return
    
    # Запрашиваем информацию для предложения стоимости
    bot.reply_to(
        message,
        f"{EMOJI['ai']} *Предложение стоимости услуг*\n\n"
        "Опишите проблему клиента и выполненные работы, и я помогу вам "
        "предложить справедливую стоимость услуг.\n\n"
        "Пример: _Не загружается Windows. Произведена замена жесткого диска, "
        "установка операционной системы и драйверов, настройка BIOS, перенос данных пользователя._\n\n"
        "Напишите /cancel для отмены.",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние ожидания ввода данных для предложения стоимости
    set_user_state(user_id, 'waiting_for_cost_suggestion')

@bot.message_handler(commands=['generate_description'])
def handle_generate_description_command(message: Message):
    """
    Обработчик команды /generate_description
    Запрашивает описание проблемы и выполненных действий для генерации профессионального отчета
    """
    user_id = message.from_user.id
    
    # Проверяем роль пользователя - должен быть диспетчером, техником или админом
    role = get_user_role(user_id)
    if role not in ['admin', 'dispatcher', 'technician']:
        bot.reply_to(message, format_error_message("Эта команда доступна только для диспетчеров, мастеров и админов."))
        return
    
    # Запрашиваем информацию для генерации отчета
    bot.reply_to(
        message,
        f"{EMOJI['ai']} *Генерация описания выполненных работ*\n\n"
        "Опишите проблему клиента и выполненные работы простыми словами, и я помогу вам "
        "составить профессиональное описание для отчета.\n\n"
        "Пример: _Клиент жаловался на медленную работу ноута. Почистил от пыли, "
        "заменил термопасту, удалил вирусы и ненужные программы, дефрагментировал диск._\n\n"
        "Напишите /cancel для отмены.",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние ожидания ввода данных для генерации описания
    set_user_state(user_id, 'waiting_for_description_generation')

@bot.message_handler(commands=['ai_help'])
def handle_ai_help_command(message: Message):
    """
    Обработчик команды /ai_help
    Показывает меню с доступными ИИ функциями
    """
    user_id = message.from_user.id
    
    # Проверяем роль пользователя
    role = get_user_role(user_id)
    if role not in ['admin', 'dispatcher', 'technician']:
        bot.reply_to(message, format_error_message("Эта команда доступна только для диспетчеров, мастеров и админов."))
        return
    
    # Отправляем меню с доступными ИИ функциями
    bot.send_message(
        user_id,
        f"{EMOJI['ai']} *ИИ-помощник сервиса*\n\n"
        "Выберите одну из доступных функций ИИ-помощника:",
        parse_mode="Markdown",
        reply_markup=get_ai_help_menu_keyboard()
    )

@bot.message_handler(commands=['technician_help'])
def handle_technician_help_command(message: Message):
    """
    Обработчик команды /technician_help
    Запрашивает описание проблемы для помощи мастеру
    """
    user_id = message.from_user.id
    
    # Проверяем роль пользователя - должен быть техником или админом
    role = get_user_role(user_id)
    if role not in ['admin', 'technician']:
        bot.reply_to(message, format_error_message("Эта команда доступна только для мастеров и админов."))
        return
    
    # Запрашиваем информацию о технической проблеме
    bot.reply_to(
        message,
        f"{EMOJI['ai']} *Помощь мастеру*\n\n"
        "Задайте любой технический вопрос, связанный с ремонтом компьютеров, "
        "и я постараюсь помочь вам с решением.\n\n"
        "Пример: _Как проверить, неисправна ли оперативная память? Какие инструменты использовать?_\n\n"
        "Напишите /cancel для отмены.",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние ожидания ввода технического вопроса
    set_user_state(user_id, 'waiting_for_technician_question')

@bot.message_handler(commands=['answer_customer'])
def handle_answer_customer_command(message: Message):
    """
    Обработчик команды /answer_customer
    Запрашивает вопрос клиента для генерации ответа
    """
    user_id = message.from_user.id
    
    # Проверяем роль пользователя - должен быть диспетчером, техником или админом
    role = get_user_role(user_id)
    if role not in ['admin', 'dispatcher', 'technician']:
        bot.reply_to(message, format_error_message("Эта команда доступна только для диспетчеров, мастеров и админов."))
        return
    
    # Запрашиваем информацию о вопросе клиента
    bot.reply_to(
        message,
        f"{EMOJI['ai']} *Помощь с ответом клиенту*\n\n"
        "Опишите вопрос клиента, и я помогу вам составить профессиональный и понятный ответ.\n\n"
        "Пример: _Клиент спрашивает, почему его компьютер быстро разряжается и как это исправить._\n\n"
        "Напишите /cancel для отмены.",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние ожидания ввода вопроса клиента
    set_user_state(user_id, 'waiting_for_customer_question')

@bot.message_handler(commands=['cancel'])
def handle_cancel_command(message: Message):
    """
    Обработчик команды /cancel
    Отменяет текущую ИИ операцию
    """
    user_id = message.from_user.id
    
    # Получаем текущее состояние пользователя
    current_state = get_user_state(user_id)
    
    # Проверяем, находится ли пользователь в одном из состояний ИИ-функций
    if current_state in AI_STATES:
        # Очищаем состояние пользователя
        clear_user_state(user_id)
        
        # Отправляем сообщение об успешной отмене
        bot.reply_to(
            message,
            format_success_message("Операция отменена. Чем еще я могу помочь?")
        )
    else:
        # Если пользователь не находится в состоянии ИИ-функции, отправляем сообщение об этом
        bot.reply_to(
            message,
            "У вас нет активных операций ИИ для отмены."
        )

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

# This function is now defined above with a decorator
# We're removing it to avoid duplication

# Функция перенесена выше с использованием декоратора

# Функция перенесена выше с использованием декоратора

# Функция перенесена выше с использованием декоратора

# Функция перенесена выше с использованием декоратора

# Функция перенесена выше с использованием декоратора

# Функция перенесена выше с использованием декоратора

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
    
def handle_ai_order_help_callback(user_id: int, message_id: int, order_id: int):
    """
    Обработчик callback-запроса ai_order_help_{order_id}
    Помощь мастеру по конкретному заказу с использованием описания проблемы из заказа
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
            
        # Получаем описание проблемы из заказа
        problem_description = order.problem_description
        
        # Если описание слишком короткое, запрашиваем дополнительную информацию
        if len(problem_description) < 20:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f"{EMOJI['info']} Описание проблемы в заказе слишком краткое.\n\n"
                f"Пожалуйста, предоставьте дополнительную информацию о проблеме:\n\n"
                f"Текущее описание: \"{problem_description}\"\n\n"
                f"Чтобы отменить, отправьте /cancel",
                parse_mode="Markdown"
            )
            # Устанавливаем состояние пользователя и сохраняем ID заказа
            set_user_state(user_id, AI_STATES['waiting_for_technician_question'])
            return
            
        # Генерируем рекомендации с помощью ИИ
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=f"{EMOJI['loading']} Анализирую проблему и формирую рекомендации...",
            parse_mode="Markdown"
        )
        
        # Используем AI для анализа проблемы
        ai_response = assist_technician(problem_description)
        
        # Форматируем ответ для отображения
        diagnostic_steps = "\n".join([f"• {step}" for step in ai_response.get("diagnostic_steps", [])])
        possible_causes = "\n".join([f"• {cause}" for cause in ai_response.get("possible_causes", [])])
        solution_steps = "\n".join([f"• {step}" for step in ai_response.get("solution_steps", [])])
        required_tools = "\n".join([f"• {tool}" for tool in ai_response.get("required_tools", [])])
        precautions = "\n".join([f"• {precaution}" for precaution in ai_response.get("precautions", [])])
        
        response_text = f"{EMOJI['ai']} *ИИ-рекомендации по заказу #{order_id}*\n\n"
        response_text += f"*Проблема:*\n{problem_description}\n\n"
        
        response_text += f"*Возможные причины:*\n{possible_causes}\n\n"
        response_text += f"*Шаги диагностики:*\n{diagnostic_steps}\n\n"
        response_text += f"*Решение:*\n{solution_steps}\n\n"
        
        if required_tools:
            response_text += f"*Необходимые инструменты:*\n{required_tools}\n\n"
            
        if precautions:
            response_text += f"*Меры предосторожности:*\n{precautions}\n\n"
        
        # Создаем клавиатуру для возврата к заказу
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🔄 Обновить рекомендации", callback_data=f"ai_order_help_{order_id}"),
            InlineKeyboardButton("📋 Вернуться к заказу", callback_data=f"order_{order_id}")
        )
        
        # Отправляем ответ
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=response_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            # Если текст слишком длинный или проблемы с форматированием
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f"{EMOJI['ai']} ИИ-рекомендации по заказу #{order_id}\n\n"
                f"Анализ проблемы завершен, но текст слишком большой.\n"
                f"Отправляю результат отдельным сообщением...",
                reply_markup=keyboard
            )
            bot.send_message(
                chat_id=user_id,
                text=response_text,
                parse_mode="Markdown"
            )
        
        # Добавляем запись в лог активности
        add_activity_log(
            user_id=user_id,
            action_type='ai_help',
            action_description=f'Получены ИИ-рекомендации по заказу #{order_id}',
            related_order_id=order_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке AI-помощи для заказа: {e}")
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=format_error_message(f"Произошла ошибка при обработке запроса: {e}"),
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode="Markdown"
        )

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