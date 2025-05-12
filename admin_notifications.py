"""
Модуль для отправки оповещений администраторам о критических событиях
"""
import logging
import traceback
from datetime import datetime
import time
import socket
import os
import json
from typing import List, Dict, Any, Optional, Union

# Импортируем логгеры
try:
    from setup_logging import admin_logger, error_logger
except ImportError:
    # Если не удалось импортировать, создаем базовый логгер
    logging.basicConfig(level=logging.INFO)
    admin_logger = logging.getLogger('admin_notifications')
    error_logger = logging.getLogger('error_notifications')

class ErrorSeverity:
    """Уровни серьезности ошибок"""
    LOW = "low"           # Незначительные ошибки
    MEDIUM = "medium"     # Ошибки, требующие внимания
    HIGH = "high"         # Серьезные ошибки
    CRITICAL = "critical" # Критические ошибки, требующие немедленного вмешательства

class ErrorNotification:
    """Класс для представления уведомления об ошибке"""
    
    def __init__(self, 
                 message: str, 
                 severity: str = ErrorSeverity.MEDIUM,
                 exception: Optional[Exception] = None,
                 traceback_info: Optional[str] = None,
                 user_id: Optional[int] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Инициализация уведомления об ошибке
        
        Args:
            message: Основное сообщение об ошибке
            severity: Уровень серьезности из ErrorSeverity
            exception: Объект исключения (если есть)
            traceback_info: Строка с трассировкой стека (если есть)
            user_id: ID пользователя, с которым связана ошибка (если есть)
            context: Дополнительная контекстная информация в виде словаря
        """
        self.message = message
        self.severity = severity
        self.exception = exception
        self.traceback_info = traceback_info
        self.timestamp = datetime.now()
        self.user_id = user_id
        self.context = context or {}
        self.hostname = socket.gethostname()
        self.environment = os.environ.get('RENDER', 'development')
        
        # Добавляем информацию о процессе
        self.process_id = os.getpid()
        
        # Добавляем хеш ошибки для группировки
        self.error_hash = self._generate_error_hash()
    
    def _generate_error_hash(self) -> str:
        """
        Генерирует уникальный хеш для ошибки, чтобы группировать похожие ошибки
        
        Returns:
            str: Хеш ошибки
        """
        import hashlib
        
        # Создаем основу для хеша из сообщения и типа исключения
        hash_base = f"{self.message}"
        
        if self.exception:
            hash_base += f"_{type(self.exception).__name__}"
            
        # Если есть трассировка, используем только первую строку для хеша
        if self.traceback_info:
            first_line = self.traceback_info.split('\n')[0]
            hash_base += f"_{first_line}"
            
        # Создаем MD5 хеш
        return hashlib.md5(hash_base.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует уведомление в словарь для сериализации
        
        Returns:
            Dict: Словарь с данными уведомления
        """
        result = {
            'message': self.message,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'hostname': self.hostname,
            'environment': self.environment,
            'process_id': self.process_id,
            'error_hash': self.error_hash
        }
        
        if self.exception:
            result['exception'] = {
                'type': type(self.exception).__name__,
                'message': str(self.exception)
            }
            
        if self.traceback_info:
            result['traceback'] = self.traceback_info
            
        if self.user_id:
            result['user_id'] = self.user_id
            
        if self.context:
            result['context'] = self.context
            
        return result
    
    def format_message_for_telegram(self) -> str:
        """
        Форматирует сообщение для отправки в Telegram
        
        Returns:
            str: Отформатированное сообщение
        """
        severity_emoji = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(self.severity, "⚠️")
        timestamp_str = self.timestamp.strftime("%d.%m.%Y %H:%M:%S")
        
        message = f"{emoji} *Ошибка: {self.severity.upper()}*\n\n"
        message += f"⏰ *Время:* {timestamp_str}\n"
        message += f"🌐 *Среда:* {self.environment}\n"
        message += f"💻 *Сервер:* {self.hostname}\n"
        message += f"📝 *Сообщение:* {self.message}\n"
        
        if self.exception:
            message += f"❌ *Исключение:* {type(self.exception).__name__}: {str(self.exception)}\n"
            
        if self.user_id:
            message += f"👤 *ID пользователя:* {self.user_id}\n"
        
        # Добавляем трассировку стека (ограниченную по длине)
        if self.traceback_info:
            max_length = 500
            traceback_short = self.traceback_info
            if len(traceback_short) > max_length:
                traceback_short = traceback_short[:max_length] + "...\n[сообщение обрезано]"
            message += f"\n```\n{traceback_short}\n```"
        
        # Добавляем контекст, если он есть
        if self.context and len(self.context) > 0:
            message += "\n*Контекст:*\n"
            for key, value in self.context.items():
                # Ограничиваем длину значения
                str_value = str(value)
                if len(str_value) > 50:
                    str_value = str_value[:50] + "..."
                message += f"- {key}: {str_value}\n"
                
        return message

# Хранилище для дедупликации ошибок
_error_cache = {}
_notification_throttle = {}

def should_send_notification(error_hash: str, min_interval_seconds: int = 300) -> bool:
    """
    Проверяет, нужно ли отправлять уведомление об ошибке,
    чтобы избежать спама одинаковыми ошибками
    
    Args:
        error_hash: Хеш ошибки
        min_interval_seconds: Минимальный интервал между уведомлениями в секундах
        
    Returns:
        bool: True, если нужно отправить уведомление
    """
    current_time = time.time()
    
    # Если ошибка ранее не встречалась, разрешаем отправку
    if error_hash not in _notification_throttle:
        _notification_throttle[error_hash] = current_time
        return True
    
    # Если прошло достаточно времени с момента последней отправки, разрешаем
    last_sent = _notification_throttle[error_hash]
    if current_time - last_sent >= min_interval_seconds:
        _notification_throttle[error_hash] = current_time
        return True
    
    # В противном случае блокируем отправку
    return False

def get_admin_user_ids() -> List[int]:
    """
    Получает список ID администраторов из базы данных
    
    Returns:
        List[int]: Список ID пользователей с ролью администратора
    """
    try:
        # Импортируем необходимые функции
        from database import get_all_users
        from config import ROLES
        
        users = get_all_users()
        admin_ids = []
        
        # Проверяем каждого пользователя
        if users:
            for user in users:
                try:
                    from database import get_user_role
                    
                    user_id = user.get('user_id') or user.get('id')
                    if user_id and get_user_role(user_id) == ROLES['admin']:
                        admin_ids.append(user_id)
                except Exception as e:
                    error_logger.error(f"Ошибка при проверке роли пользователя: {e}")
        
        return admin_ids
    except Exception as e:
        error_logger.error(f"Ошибка при получении списка администраторов: {e}")
        # Возвращаем пустой список в случае ошибки
        return []

def notify_admins_about_error(message: str, 
                             severity: str = ErrorSeverity.MEDIUM,
                             exception: Optional[Exception] = None,
                             user_id: Optional[int] = None,
                             context: Optional[Dict[str, Any]] = None,
                             force: bool = False) -> bool:
    """
    Отправляет уведомление об ошибке всем администраторам
    
    Args:
        message: Сообщение об ошибке
        severity: Уровень серьезности ошибки
        exception: Объект исключения (если есть)
        user_id: ID пользователя, с которым связана ошибка
        context: Дополнительная информация
        force: Принудительно отправить, игнорируя тротлинг
        
    Returns:
        bool: True, если уведомление отправлено хотя бы одному администратору
    """
    # Получаем информацию о стеке вызовов, если есть исключение
    traceback_info = None
    if exception:
        traceback_info = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    
    # Создаем объект уведомления
    notification = ErrorNotification(
        message=message,
        severity=severity,
        exception=exception,
        traceback_info=traceback_info,
        user_id=user_id,
        context=context
    )
    
    # Логируем ошибку
    if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
        error_logger.error(message, exc_info=True if exception else False)
    else:
        error_logger.warning(message, exc_info=True if exception else False)
    
    # Проверяем, нужно ли отправлять уведомление (защита от спама)
    if not force and not should_send_notification(notification.error_hash):
        error_logger.info(f"Уведомление с хешем {notification.error_hash} пропущено (тротлинг)")
        return False
    
    # Получаем ID администраторов
    admin_ids = get_admin_user_ids()
    
    # Если нет администраторов, логируем это и выходим
    if not admin_ids:
        error_logger.warning("Не найдены администраторы для отправки уведомления об ошибке")
        return False
    
    # Форматируем сообщение для Telegram
    telegram_message = notification.format_message_for_telegram()
    
    # Отправляем сообщение каждому администратору
    success = False
    try:
        from shared_state import bot
        
        for admin_id in admin_ids:
            try:
                bot.send_message(admin_id, telegram_message, parse_mode="Markdown")
                admin_logger.info(f"Уведомление об ошибке отправлено администратору {admin_id}")
                success = True
            except Exception as e:
                error_logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
    except Exception as e:
        error_logger.error(f"Ошибка при отправке уведомлений: {e}")
    
    return success

# Вспомогательные функции для быстрого вызова с разной серьезностью
def notify_info(message: str, **kwargs):
    """Отправляет информационное уведомление"""
    return notify_admins_about_error(message, severity=ErrorSeverity.LOW, **kwargs)

def notify_warning(message: str, **kwargs):
    """Отправляет предупреждение"""
    return notify_admins_about_error(message, severity=ErrorSeverity.MEDIUM, **kwargs)

def notify_error(message: str, **kwargs):
    """Отправляет уведомление о серьезной ошибке"""
    return notify_admins_about_error(message, severity=ErrorSeverity.HIGH, **kwargs)

def notify_critical(message: str, **kwargs):
    """Отправляет уведомление о критической ошибке"""
    return notify_admins_about_error(message, severity=ErrorSeverity.CRITICAL, **kwargs)

# Функция для логирования действий администратора
def log_admin_action(admin_id: int, action: str, target_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
    """
    Логирует действие администратора
    
    Args:
        admin_id: ID администратора, выполнившего действие
        action: Название действия
        target_id: ID объекта, над которым выполнено действие (пользователь, заказ и т.д.)
        details: Дополнительные сведения о действии
    """
    log_data = {
        'admin_id': admin_id,
        'action': action,
        'timestamp': datetime.now().isoformat()
    }
    
    if target_id is not None:
        log_data['target_id'] = target_id
        
    if details:
        log_data['details'] = details
    
    # Логируем действие
    admin_logger.info(json.dumps(log_data))
    
    # Если это важное действие, отправляем уведомление другим администраторам
    important_actions = ['delete_user', 'delete_order', 'add_admin', 'block_user']
    if action in important_actions:
        try:
            from database import get_user
            admin = get_user(admin_id)
            admin_name = f"{admin.get('first_name', '')} {admin.get('last_name', '')}"
            
            # Формируем сообщение
            if action == 'delete_user' and target_id:
                target = get_user(target_id)
                target_name = f"{target.get('first_name', '')} {target.get('last_name', '')}"
                message = f"Администратор {admin_name} удалил пользователя {target_name} (ID: {target_id})"
            elif action == 'delete_order' and target_id:
                message = f"Администратор {admin_name} удалил заказ #{target_id}"
            elif action == 'add_admin' and target_id:
                target = get_user(target_id)
                target_name = f"{target.get('first_name', '')} {target.get('last_name', '')}"
                message = f"Администратор {admin_name} назначил пользователя {target_name} (ID: {target_id}) администратором"
            elif action == 'block_user' and target_id:
                target = get_user(target_id)
                target_name = f"{target.get('first_name', '')} {target.get('last_name', '')}"
                message = f"Администратор {admin_name} заблокировал пользователя {target_name} (ID: {target_id})"
            else:
                message = f"Администратор {admin_name} выполнил действие {action}"
                if target_id:
                    message += f" с объектом ID: {target_id}"
                    
            # Добавляем детали, если они есть
            if details:
                message += "\nДетали: " + json.dumps(details, ensure_ascii=False)
                
            # Отправляем уведомление
            notify_info(message, user_id=admin_id)
        except Exception as e:
            error_logger.error(f"Ошибка при отправке уведомления о действии администратора: {e}")

# Пример использования
if __name__ == "__main__":
    # Тестовое уведомление
    notify_warning("Тестовое предупреждение", context={"test": True})
    
    try:
        # Генерируем исключение для теста
        1/0
    except Exception as e:
        notify_error("Произошла ошибка деления на ноль", exception=e)
        
    print("Тесты уведомлений администраторам выполнены.")