"""
Модуль настройки системы логирования для приложения
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime

# Константы для уровней логирования
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Директория для хранения логов
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Форматы логов
CONSOLE_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
FILE_FORMAT = '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'

# Цвета для консольного вывода
COLORS = {
    'DEBUG': '\033[94m',  # Синий
    'INFO': '\033[92m',   # Зеленый
    'WARNING': '\033[93m', # Желтый
    'ERROR': '\033[91m',  # Красный
    'CRITICAL': '\033[1;91m', # Яркий красный
    'ENDC': '\033[0m'     # Сброс цвета
}

class ColoredFormatter(logging.Formatter):
    """Форматер, добавляющий цвета в лог-сообщения для консоли"""
    def format(self, record):
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['ENDC']}"
        return super().format(record)

def setup_logger(name, level=logging.INFO, console_level=None, file_level=None):
    """
    Настраивает и возвращает логгер с заданным именем и уровнем логирования
    
    Args:
        name (str): Имя логгера
        level (int): Общий уровень логирования (по умолчанию INFO)
        console_level (int): Уровень логирования для консоли, если отличается от общего
        file_level (int): Уровень логирования для файла, если отличается от общего
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Очищаем обработчики, если они уже были добавлены
    if logger.handlers:
        logger.handlers.clear()
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level if console_level is not None else level)
    console_formatter = ColoredFormatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик с ротацией
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5            # 5 резервных копий
    )
    file_handler.setLevel(file_level if file_level is not None else level)
    file_formatter = logging.Formatter(FILE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_component_logger(component_name, level=logging.INFO):
    """
    Возвращает логгер для конкретного компонента системы
    
    Args:
        component_name (str): Имя компонента (database, bot, api и т.д.)
        level (int): Уровень логирования для компонента
    
    Returns:
        logging.Logger: Настроенный логгер для компонента
    """
    return setup_logger(f"service.{component_name}", level)

# Основной логгер приложения
main_logger = setup_logger('service', logging.INFO)

def log_function_call(logger):
    """
    Декоратор для логирования вызовов функций
    
    Args:
        logger (logging.Logger): Логгер для записи информации
    
    Returns:
        function: Декоратор
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Вызов функции: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"Функция {func.__name__} выполнена за {execution_time:.4f} сек")
                return result
            except Exception as e:
                logger.error(f"Ошибка в функции {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator