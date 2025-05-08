"""
Модуль для общих функций состояния, используемых между различными модулями бота
"""

from typing import Optional
import os
import telebot
from logger import get_component_logger, log_function_call

# Настройка логирования
logger = get_component_logger('shared_state')

# Создаем экземпляр бота
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# Проверка на наличие токена, чтобы избежать ошибок
if TOKEN is None:
    logger.error("Ошибка: Токен Telegram бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
    TOKEN = "dummy_token"  # Временный токен, чтобы избежать ошибок инициализации
    
bot = telebot.TeleBot(TOKEN)

def init_bot(bot_instance):
    """Инициализирует переменную bot"""
    global bot
    bot = bot_instance

@log_function_call(logger)
def set_user_state(user_id: int, state: str, order_id: Optional[int] = None) -> None:
    """
    Устанавливает состояние пользователя
    """
    from database import set_user_state as db_set_user_state
    logger.debug(f"Установка состояния для пользователя {user_id}: {state}, order_id={order_id}")
    db_set_user_state(user_id, state, order_id)

@log_function_call(logger)
def clear_user_state(user_id: int) -> None:
    """
    Очищает состояние пользователя
    """
    from database import clear_user_state as db_clear_user_state
    logger.debug(f"Очистка состояния для пользователя {user_id}")
    db_clear_user_state(user_id)

@log_function_call(logger)
def get_user_state(user_id: int) -> Optional[str]:
    """
    Возвращает текущее состояние пользователя
    """
    from database import get_user_state as db_get_user_state
    state = db_get_user_state(user_id)
    logger.debug(f"Получено состояние пользователя {user_id}: {state}")
    return state

@log_function_call(logger)
def get_current_order_id(user_id: int) -> Optional[int]:
    """
    Возвращает ID текущего заказа пользователя
    """
    from database import get_current_order_id as db_get_current_order_id
    order_id = db_get_current_order_id(user_id)
    logger.debug(f"Получен текущий order_id для пользователя {user_id}: {order_id}")
    return order_id