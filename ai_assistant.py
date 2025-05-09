"""
Модуль для интеграции ИИ (OpenAI) в функционал Telegram бота
"""
import os
import json
import re
from typing import Dict, List, Optional, Any

from openai import OpenAI
from logger import get_component_logger

# Настройка логгера
logger = get_component_logger('ai_assistant')

# AI функции отключены
client = None

# Константы для моделей
DEFAULT_MODEL = "gpt-4o"  # Используем последнюю модель
EMBEDDING_MODEL = "text-embedding-3-small"

def generate_response(prompt: str, system_message: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 500) -> str:
    return "AI функции временно отключены"
    """
    Генерирует ответ на основе промпта с использованием GPT модели
    
    Args:
        prompt: Текстовый запрос
        system_message: Системное сообщение для настройки поведения модели
        temperature: Температура генерации (0-1)
        max_tokens: Максимальное количество токенов в ответе
        
    Returns:
        str: Сгенерированный ответ
    """
    try:
        messages = []
        
        # Добавляем системное сообщение, если оно предоставлено
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        # Добавляем запрос пользователя
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {e}")
        return f"Извините, произошла ошибка при обработке запроса: {str(e)}"

def generate_json_response(prompt: str, system_message: str, 
                           temperature: float = 0.2) -> Dict[str, Any]:
    return {"message": "AI функции временно отключены"}
    """
    Генерирует структурированный JSON ответ
    
    Args:
        prompt: Текстовый запрос
        system_message: Системное сообщение с описанием формата JSON
        temperature: Температура генерации (0-1)
        
    Returns:
        Dict: Структурированный ответ в формате словаря
    """
    try:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Ошибка при генерации JSON ответа: {e}")
        return {"error": str(e)}

def analyze_problem_description(description: str) -> Dict[str, Any]:
    """
    Анализирует описание проблемы и возвращает структурированную информацию
    
    Args:
        description: Текстовое описание проблемы
        
    Returns:
        Dict: Структурированная информация о проблеме
    """
    system_message = """
    Ты аналитик технических проблем с компьютерами. Проанализируй описание 
    проблемы и верни JSON со следующей структурой:
    {
        "category": "Одна из категорий: hardware, software, network, peripheral, other",
        "severity": "Число от 1 до 5, где 1 - минимальная, 5 - критическая",
        "estimated_time": "Примерное время на решение в часах",
        "required_parts": ["Список необходимых запчастей или пусто"],
        "possible_solutions": ["Список возможных решений"],
        "questions": ["Дополнительные вопросы для уточнения проблемы"] 
    }
    """
    
    return generate_json_response(description, system_message)

def suggest_service_cost(problem_description: str, 
                         service_description: Optional[str] = None) -> Dict[str, Any]:
    """
    Предлагает стоимость услуг на основе описания проблемы и выполненных работ
    
    Args:
        problem_description: Описание проблемы
        service_description: Описание выполненных работ (если есть)
        
    Returns:
        Dict: Рекомендации по стоимости услуг
    """
    combined_text = problem_description
    if service_description:
        combined_text += f"\n\nВыполненные работы: {service_description}"
    
    system_message = """
    Ты эксперт по ценообразованию услуг ремонта компьютеров. На основе описания
    проблемы и выполненных работ (если указаны) предложи стоимость услуг.
    Верни ответ как JSON объект с полями:
    {
        "min_cost": "Минимальная стоимость в рублях",
        "max_cost": "Максимальная стоимость в рублях",
        "recommended_cost": "Рекомендуемая стоимость в рублях",
        "complexity": "Сложность работ (1-5)",
        "justification": "Краткое обоснование стоимости"
    }
    """
    
    return generate_json_response(combined_text, system_message)

def generate_service_description(problem_description: str, 
                                fix_actions: List[str]) -> str:
    """
    Генерирует профессиональное описание выполненных работ
    
    Args:
        problem_description: Описание исходной проблемы
        fix_actions: Список выполненных действий
        
    Returns:
        str: Профессиональное описание выполненных работ
    """
    prompt = f"""
    Исходная проблема: {problem_description}
    
    Выполненные действия:
    """ + '\n'.join([f'- {action}' for action in fix_actions]) + """
    
    Сгенерируй профессиональное описание выполненных работ для отчета.
    """
    
    system_message = """
    Ты профессиональный инженер сервиса по ремонту компьютеров. Составь грамотное
    и профессиональное описание выполненных работ на основе предоставленной информации.
    Описание должно:
    1. Быть структурированным и четким
    2. Использовать профессиональную терминологию
    3. Описывать как диагностику, так и решение проблемы
    4. Быть понятным клиенту, но при этом демонстрировать профессионализм
    """
    
    return generate_response(prompt, system_message)

def summarize_order_history(order_logs: List[Dict[str, Any]]) -> str:
    """
    Создает краткую сводку по истории заказа
    
    Args:
        order_logs: Список записей логов, связанных с заказом
        
    Returns:
        str: Краткая сводка по истории заказа
    """
    # Преобразуем логи в текстовый формат для обработки
    logs_text = ""
    for log in order_logs:
        timestamp = log.get('created_at', '').strftime("%d.%m.%Y %H:%M") if log.get('created_at') else 'Н/Д'
        user = f"{log.get('first_name', '')} {log.get('last_name', '')}".strip() or 'Неизвестный пользователь'
        action = log.get('action_description', 'Действие не указано')
        logs_text += f"{timestamp}: {user} - {action}\n"
    
    prompt = f"""
    История заказа:
    {logs_text}
    
    Создай краткую сводку по истории заказа, выделив ключевые этапы и события.
    """
    
    system_message = """
    Ты аналитик данных сервисного центра. Твоя задача - создать краткую 
    и информативную сводку истории заказа на основе логов действий.
    Выдели ключевые этапы:
    1. Создание заказа
    2. Назначение мастера
    3. Изменения статуса
    4. Обновления информации
    5. Завершение или отмена
    """
    
    return generate_response(prompt, system_message)

def answer_customer_question(question: str, order_data: Dict[str, Any]) -> str:
    """
    Генерирует ответ на вопрос клиента с учетом данных заказа
    
    Args:
        question: Вопрос клиента
        order_data: Данные заказа
        
    Returns:
        str: Ответ на вопрос клиента
    """
    # Формируем контекст с информацией о заказе
    order_context = json.dumps(order_data, ensure_ascii=False, default=str)
    
    prompt = f"""
    Информация о заказе:
    {order_context}
    
    Вопрос клиента: {question}
    
    Предоставь исчерпывающий и вежливый ответ на вопрос клиента с учетом информации о заказе.
    """
    
    system_message = """
    Ты вежливый и профессиональный менеджер клиентской поддержки сервиса по ремонту компьютеров.
    Твоя задача - отвечать на вопросы клиентов о их заказах на ремонт.
    Используй предоставленную информацию о заказе, чтобы дать точный ответ.
    Будь вежливым, информативным и профессиональным.
    Если ты не можешь ответить на вопрос на основе предоставленной информации,
    предложи клиенту связаться с диспетчером или мастером для получения дополнительной информации.
    """
    
    return generate_response(prompt, system_message)

def detect_order_anomalies(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Выявляет аномалии и потенциальные проблемы в заказах
    
    Args:
        orders: Список заказов
        
    Returns:
        List[Dict]: Список обнаруженных аномалий
    """
    # Преобразуем заказы в текстовый формат
    orders_text = json.dumps(orders, ensure_ascii=False, default=str)
    
    system_message = """
    Ты аналитик данных сервисного центра по ремонту компьютеров. Твоя задача - 
    выявить аномалии и потенциальные проблемы в списке заказов.
    
    Обрати внимание на:
    1. Заказы, "застрявшие" в одном статусе слишком долго
    2. Заказы без назначенного мастера
    3. Заказы с очень длительным сроком выполнения
    4. Заказы с необычно высокой или низкой стоимостью
    5. Заказы с неполной информацией
    
    Верни JSON-объект со следующей структурой:
    {
        "anomalies": [
            {
                "order_id": "ID заказа",
                "issue_type": "Тип проблемы",
                "description": "Описание проблемы",
                "severity": "Серьезность (low, medium, high)",
                "recommendation": "Рекомендация по решению"
            }
        ]
    }
    """
    
    prompt = f"""
    Проанализируй следующий список заказов на ремонт компьютеров:
    {orders_text}
    
    Выяви аномалии и потенциальные проблемы согласно указанным критериям.
    """
    
    result = generate_json_response(prompt, system_message)
    return result.get("anomalies", [])

def assist_technician(problem_description: str, 
                      technician_notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Помогает мастеру с диагностикой и решением проблемы
    
    Args:
        problem_description: Описание проблемы
        technician_notes: Заметки мастера о проблеме (если есть)
        
    Returns:
        Dict: Рекомендации по диагностике и решению
    """
    combined_text = f"Описание проблемы клиентом: {problem_description}"
    if technician_notes:
        combined_text += f"\n\nЗаметки мастера: {technician_notes}"
    
    system_message = """
    Ты опытный технический специалист по ремонту компьютеров. На основе описания
    проблемы и заметок мастера (если есть) предложи план диагностики и решения.
    
    Верни ответ как JSON со следующей структурой:
    {
        "diagnostic_steps": ["Шаги для диагностики проблемы"],
        "possible_causes": ["Возможные причины проблемы"],
        "solution_steps": ["Рекомендуемые шаги для решения"],
        "required_tools": ["Необходимые инструменты"],
        "precautions": ["Меры предосторожности"],
        "additional_resources": ["Ссылки на полезные ресурсы или мануалы"]
    }
    """
    
    return generate_json_response(combined_text, system_message)

def analyze_service_performance(technician_id: str, 
                               completed_orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует эффективность работы мастера на основе выполненных заказов
    
    Args:
        technician_id: ID мастера
        completed_orders: Список выполненных заказов
        
    Returns:
        Dict: Анализ эффективности работы
    """
    # Преобразуем заказы в текстовый формат
    orders_text = json.dumps(completed_orders, ensure_ascii=False, default=str)
    
    system_message = """
    Ты аналитик эффективности работы сервисного центра. Проанализируй список
    выполненных заказов мастера и оцени его эффективность.
    
    Верни JSON со следующей структурой:
    {
        "average_completion_time": "Среднее время выполнения заказа в часах",
        "most_common_issues": ["Наиболее частые проблемы"],
        "average_cost": "Средняя стоимость услуг",
        "efficiency_score": "Оценка эффективности от 1 до 10",
        "strengths": ["Сильные стороны мастера"],
        "areas_for_improvement": ["Области для улучшения"],
        "recommendations": ["Рекомендации по повышению эффективности"]
    }
    """
    
    prompt = f"""
    Проанализируй следующий список заказов, выполненных мастером {technician_id}:
    {orders_text}
    
    Оцени эффективность работы мастера на основе времени выполнения, сложности проблем,
    стоимости услуг и других факторов, которые ты сможешь выявить.
    """
    
    return generate_json_response(prompt, system_message)

def categorize_orders(orders_batch: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Автоматически категоризирует заказы по типу проблемы
    
    Args:
        orders_batch: Список заказов
        
    Returns:
        Dict: Словарь с категориями и списками ID заказов
    """
    # Преобразуем заказы в текстовый формат
    orders_text = json.dumps(orders_batch, ensure_ascii=False, default=str)
    
    system_message = """
    Ты специалист по классификации технических проблем с компьютерами.
    Проанализируй описания проблем в заказах и распредели их по категориям.
    
    Категории:
    - hardware: проблемы с аппаратной частью (диски, память, процессор и т.д.)
    - software: проблемы с программным обеспечением, ОС, приложениями
    - network: проблемы с сетью, интернет-соединением, Wi-Fi
    - peripheral: проблемы с периферийными устройствами (принтеры, сканеры и т.д.)
    - virus: проблемы с вирусами, вредоносным ПО
    - data: проблемы с данными, восстановление данных
    - other: прочие проблемы
    
    Верни JSON со следующей структурой:
    {
        "hardware": [список ID заказов],
        "software": [список ID заказов],
        "network": [список ID заказов],
        "peripheral": [список ID заказов],
        "virus": [список ID заказов],
        "data": [список ID заказов],
        "other": [список ID заказов]
    }
    """
    
    prompt = f"""
    Проанализируй следующие заказы на ремонт компьютеров и распредели их по
    указанным категориям на основе описания проблем:
    
    {orders_text}
    """
    
    return generate_json_response(prompt, system_message)

def extract_client_info(text: str) -> Dict[str, str]:
    """
    Извлекает информацию о клиенте из неструктурированного текста
    
    Args:
        text: Неструктурированный текст с информацией о клиенте
        
    Returns:
        Dict: Структурированная информация о клиенте
    """
    system_message = """
    Ты эксперт по обработке данных. Твоя задача - извлечь информацию о клиенте
    из неструктурированного текста. Найди все доступные контактные данные и
    информацию о клиенте.
    
    Верни JSON со следующей структурой:
    {
        "name": "Имя клиента или null, если не найдено",
        "phone": "Номер телефона или null, если не найден",
        "address": "Адрес или null, если не найден",
        "email": "Email или null, если не найден",
        "additional_info": "Любая дополнительная информация или null"
    }
    
    Предварительно обработай телефонные номера, чтобы они были в формате +7XXXXXXXXXX.
    """
    
    prompt = f"""
    Извлеки информацию о клиенте из следующего текста:
    {text}
    """
    
    return generate_json_response(prompt, system_message)