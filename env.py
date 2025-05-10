"""
Модуль для загрузки переменных окружения.
Используется для локальной разработки.
"""

import os
import sys

# Загрузка переменных окружения для Render из .env_render
if os.path.exists('.env_render'):
    print("Загрузка переменных окружения из .env_render")
    with open('.env_render', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                # Разбиваем по первому символу '='
                parts = line.strip().split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    # Удаляем export, если есть
                    if key.startswith('export '):
                        key = key[len('export '):].strip()
                    
                    value = parts[1].strip()
                    # Удаляем кавычки, если они есть
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Устанавливаем переменную окружения
                    os.environ[key] = value
                    print(f"Переменная окружения {key} установлена, длина: {len(value)}")

# Добавляем флаг, что мы находимся в Render-подобной среде для тестирования
os.environ['RENDER'] = 'true'
print("Установлена переменная RENDER=true")