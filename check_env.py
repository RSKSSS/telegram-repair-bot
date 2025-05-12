"""
Проверка наличия необходимых переменных окружения
"""
import os
import sys

# Список обязательных переменных
REQUIRED_ENV_VARS = [
    'TELEGRAM_BOT_TOKEN'
]

# Список дополнительных переменных (не обязательных)
OPTIONAL_ENV_VARS = [
    'PORT',
    'RENDER'
]

def main():
    """Проверяет наличие переменных окружения и выводит их статус"""
    print("=== Проверка переменных окружения ===")
    
    # Проверка обязательных переменных
    missing_vars = []
    for var_name in REQUIRED_ENV_VARS:
        value = os.environ.get(var_name)
        if value:
            masked_value = value[:4] + '*' * (len(value) - 4) if len(value) > 8 else '****'
            print(f"✅ {var_name}: {masked_value}")
        else:
            missing_vars.append(var_name)
            print(f"❌ {var_name}: Не задано")
    
    # Проверка дополнительных переменных
    for var_name in OPTIONAL_ENV_VARS:
        value = os.environ.get(var_name)
        if value:
            print(f"✅ {var_name}: {value}")
        else:
            print(f"⚠️ {var_name}: Не задано (опционально)")
    
    # Выводим результат
    if missing_vars:
        print("\n⚠️ Отсутствуют обязательные переменные окружения:")
        for var_name in missing_vars:
            print(f"  - {var_name}")
        print("\nНеобходимо добавить их в настройках сервиса на Render.")
        return False
    else:
        print("\n✅ Все обязательные переменные окружения настроены.")
        return True

if __name__ == "__main__":
    if not main():
        sys.exit(1)