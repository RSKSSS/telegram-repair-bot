"""
Модуль для кэширования данных
Используется для уменьшения числа обращений к базе данных
"""

import time
from typing import Dict, Any, Callable, Tuple, List, Optional
from functools import wraps
from logger import get_component_logger

# Настройка логирования
logger = get_component_logger('cache')

# Основной словарь для хранения кэша
_cache: Dict[str, Dict[str, Any]] = {
    'users': {},       # Кэш пользователей
    'orders': {},      # Кэш заказов
    'technicians': {}, # Кэш мастеров
    'assignments': {}, # Кэш назначений
    'stats': {},       # Кэш статистики
    'misc': {}         # Прочий кэш
}

# TTL (Time To Live) для различных типов кэша в секундах
_cache_ttl: Dict[str, int] = {
    'users': 60,        # 1 минута для пользователей
    'orders': 30,       # 30 секунд для заказов
    'technicians': 60,  # 1 минута для мастеров
    'assignments': 30,  # 30 секунд для назначений
    'stats': 300,       # 5 минут для статистики
    'misc': 60          # 1 минута для прочего кэша
}

# Метки времени для отслеживания последнего обновления кэша
_last_update: Dict[str, Dict[str, float]] = {
    'users': {},
    'orders': {},
    'technicians': {},
    'assignments': {},
    'stats': {},
    'misc': {}
}

def cache_get(cache_type: str, key: str) -> Optional[Any]:
    """
    Получает значение из кэша
    
    Args:
        cache_type: Тип кэша ('users', 'orders', etc.)
        key: Ключ для доступа к кэшу
        
    Returns:
        Any: Значение из кэша или None, если его нет или оно устарело
    """
    if cache_type not in _cache:
        logger.warning(f"Попытка получить данные из несуществующего типа кэша: {cache_type}")
        return None
        
    # Проверяем, есть ли ключ в кэше данного типа
    if key not in _cache[cache_type]:
        return None
        
    # Проверяем, устарел ли кэш
    now = time.time()
    ttl = _cache_ttl.get(cache_type, 60)  # По умолчанию 1 минута
    last_update = _last_update[cache_type].get(key, 0)
    
    if now - last_update > ttl:
        # Кэш устарел, удаляем его
        del _cache[cache_type][key]
        if key in _last_update[cache_type]:
            del _last_update[cache_type][key]
        return None
        
    return _cache[cache_type][key]

def cache_set(cache_type: str, key: str, value: Any) -> None:
    """
    Сохраняет значение в кэш
    
    Args:
        cache_type: Тип кэша ('users', 'orders', etc.)
        key: Ключ для доступа к кэшу
        value: Значение для сохранения в кэш
    """
    if cache_type not in _cache:
        logger.warning(f"Попытка сохранить данные в несуществующий тип кэша: {cache_type}")
        return
        
    # Обновляем кэш
    _cache[cache_type][key] = value
    _last_update[cache_type][key] = time.time()

def cache_delete(cache_type: str, key: str) -> None:
    """
    Удаляет значение из кэша
    
    Args:
        cache_type: Тип кэша ('users', 'orders', etc.)
        key: Ключ для доступа к кэшу
    """
    if cache_type not in _cache:
        logger.warning(f"Попытка удалить данные из несуществующего типа кэша: {cache_type}")
        return
        
    # Удаляем значение из кэша, если оно есть
    if key in _cache[cache_type]:
        del _cache[cache_type][key]
        
    # Удаляем метку времени, если она есть
    if key in _last_update[cache_type]:
        del _last_update[cache_type][key]

def cache_clear(cache_type: Optional[str] = None) -> None:
    """
    Очищает кэш определенного типа или весь кэш
    
    Args:
        cache_type: Тип кэша для очистки или None для очистки всего кэша
    """
    if cache_type is None:
        # Очищаем весь кэш
        for cache_key in _cache:
            _cache[cache_key].clear()
            _last_update[cache_key].clear()
        logger.info("Весь кэш очищен")
    elif cache_type in _cache:
        # Очищаем кэш определенного типа
        _cache[cache_type].clear()
        _last_update[cache_type].clear()
        logger.info(f"Кэш типа {cache_type} очищен")
    else:
        logger.warning(f"Попытка очистить несуществующий тип кэша: {cache_type}")

def cached(cache_type: str, key_func: Callable = None) -> Callable:
    """
    Декоратор для кэширования результатов функций
    
    Args:
        cache_type: Тип кэша
        key_func: Функция для генерации ключа кэша (если не указана, используется первый аргумент)
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            elif args:
                # По умолчанию используем первый аргумент как ключ
                cache_key = str(args[0])
            else:
                # Если нет аргументов, используем имя функции
                cache_key = func.__name__
                
            # Проверяем, есть ли результат в кэше
            cached_value = cache_get(cache_type, cache_key)
            if cached_value is not None:
                logger.debug(f"Использован кэш для {func.__name__}, ключ: {cache_key}")
                return cached_value
                
            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            if result is not None:  # Кэшируем только непустые результаты
                cache_set(cache_type, cache_key, result)
                logger.debug(f"Добавлен кэш для {func.__name__}, ключ: {cache_key}")
                
            return result
        return wrapper
    return decorator

def invalidate_cache_on_update(cache_type: str, key_func: Callable = None) -> Callable:
    """
    Декоратор для инвалидации кэша при обновлении данных
    
    Args:
        cache_type: Тип кэша для инвалидации
        key_func: Функция для генерации ключа кэша (если не указана, используется первый аргумент)
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            elif args:
                # По умолчанию используем первый аргумент как ключ
                cache_key = str(args[0])
            else:
                # Если нет аргументов, удаляем весь кэш данного типа
                cache_clear(cache_type)
                return result
                
            # Инвалидируем кэш
            cache_delete(cache_type, cache_key)
            logger.debug(f"Инвалидирован кэш типа {cache_type}, ключ: {cache_key}")
                
            return result
        return wrapper
    return decorator