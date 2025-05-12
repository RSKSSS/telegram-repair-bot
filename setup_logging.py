"""
Настройка системы логирования для Telegram бота
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback
import json
from datetime import datetime

# Создаем директорию для логов, если её нет
LOG_FOLDER = 'logs'
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Подпапки для разных типов логов
ERROR_LOG_FOLDER = os.path.join(LOG_FOLDER, 'errors')
if not os.path.exists(ERROR_LOG_FOLDER):
    os.makedirs(ERROR_LOG_FOLDER)

ADMIN_LOG_FOLDER = os.path.join(LOG_FOLDER, 'admin')
if not os.path.exists(ADMIN_LOG_FOLDER):
    os.makedirs(ADMIN_LOG_FOLDER)

# Конфигурация основного логгера
def setup_logger(name, log_file, level=logging.INFO, max_size=5*1024*1024, backup_count=5):
    """Настройка логгера с ротацией файлов по размеру"""
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count
    )
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    # Добавляем вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Настройка логгера для ежедневной ротации
def setup_daily_logger(name, log_file, level=logging.INFO, backup_count=30):
    """Настройка логгера с ежедневной ротацией"""
    handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=backup_count
    )
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# Настройка JSON-логгера для структурированного логирования
def setup_json_logger(name, log_file, level=logging.INFO, max_size=2*1024*1024, backup_count=5):
    """Настройка логгера с JSON-форматированием для аналитики"""
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count
    )
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'line': record.lineno
            }
            
            if hasattr(record, 'user_id'):
                log_record['user_id'] = record.user_id
                
            if hasattr(record, 'action'):
                log_record['action'] = record.action
                
            if hasattr(record, 'extra_data'):
                log_record['extra_data'] = record.extra_data
                
            # Добавляем информацию об исключении, если оно есть
            if record.exc_info:
                log_record['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': traceback.format_exception(*record.exc_info)
                }
                
            return json.dumps(log_record)
    
    handler.setFormatter(JsonFormatter())
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# Настраиваем логгеры для разных типов логов
main_logger = setup_logger('telegram_bot', os.path.join(LOG_FOLDER, 'bot.log'), level=logging.INFO)
error_logger = setup_logger('telegram_bot.error', os.path.join(ERROR_LOG_FOLDER, 'errors.log'), level=logging.ERROR)
api_logger = setup_logger('telegram_bot.api', os.path.join(LOG_FOLDER, 'api.log'), level=logging.INFO)
db_logger = setup_logger('telegram_bot.db', os.path.join(LOG_FOLDER, 'database.log'), level=logging.INFO)
admin_logger = setup_daily_logger('telegram_bot.admin', os.path.join(ADMIN_LOG_FOLDER, 'admin_actions.log'), level=logging.INFO)
analytics_logger = setup_json_logger('telegram_bot.analytics', os.path.join(LOG_FOLDER, 'analytics.json'), level=logging.INFO)

# Глобальный перехватчик исключений для записи в лог
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Обрабатывает необработанные исключения и записывает их в лог"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Стандартное поведение для прерывания с клавиатуры
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    error_logger.critical(
        f"Необработанное исключение: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Записываем в аналитический лог
    log_record = logging.LogRecord(
        name='telegram_bot.error',
        level=logging.CRITICAL,
        pathname=__file__,
        lineno=0,
        msg=f"Необработанное исключение: {exc_type.__name__}: {exc_value}",
        args=(),
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    analytics_logger.handle(log_record)

# Устанавливаем глобальный обработчик исключений
sys.excepthook = global_exception_handler

# Экспортируем все логгеры
__all__ = [
    'main_logger', 
    'error_logger', 
    'api_logger', 
    'db_logger', 
    'admin_logger', 
    'analytics_logger',
    'global_exception_handler'
]

# Информация о настройке логирования
if __name__ == "__main__":
    print(f"Настройка логирования завершена. Логи будут сохраняться в папке {os.path.abspath(LOG_FOLDER)}")
    main_logger.info("Система логирования инициализирована")
    error_logger.info("Система логирования ошибок инициализирована")
    api_logger.info("Система логирования API инициализирована")
    db_logger.info("Система логирования базы данных инициализирована")
    admin_logger.info("Система логирования действий администратора инициализирована")
    analytics_logger.info("Система аналитического логирования инициализирована")