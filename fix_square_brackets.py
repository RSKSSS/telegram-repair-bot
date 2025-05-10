#!/usr/bin/env python3
"""
Скрипт для исправления ошибок с квадратными скобками в файле bot_fixed2.py
"""
import re

def fix_square_brackets(file_path, output_path=None):
    """
    Исправляет ошибки с квадратными скобками в файле.
    
    Args:
        file_path: Путь к исходному файлу
        output_path: Путь для сохранения исправленного файла (если None, то перезаписывает исходный)
    """
    if output_path is None:
        output_path = file_path
        
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Заменяем неправильные обращения к элементам словаря или методам
    # Pattern: word["другоеслово"]X -> word.X или word["другоеслово"] -> word["другоеслово"]
    pattern = r'(\w+)\["(\w+)"\](\w+)'
    
    def replace_brackets(match):
        prefix = match.group(1)
        middle = match.group(2)
        suffix = match.group(3)
        
        # Если суффикс начинается с точки или круглой скобки - это метод
        if suffix.startswith('.') or suffix.startswith('('):
            return f"{prefix}.{middle}{suffix}"
        else:
            return f"{prefix}[\"{middle}\"].{suffix}"
            
    # Исправляем f-строки с двойными кавычками в квадратных скобках словаря
    f_string_pattern = r'f"([^"]*){([^}]+)\["([^"]+)"\]([^}]*)}"'
    
    def replace_f_strings(match):
        prefix = match.group(1)
        var_name = match.group(2)
        key = match.group(3)
        suffix = match.group(4)
        return f'f"{prefix}{{{var_name}[\'{key}\']{suffix}}}"'
    
    # Применяем замену для f-строк
    fixed_content = re.sub(f_string_pattern, replace_f_strings, content)
    
    # Затем применяем замену для методов
    fixed_content = re.sub(pattern, replace_brackets, fixed_content)
    
    # Исправляем конкретные случаи, которые могут быть неверно обработаны общим паттерном
    specific_replacements = [
        (r'(\w+)\["ORDER_STATUSES"\]\.get\(\)', r'\1["status"]'),
        (r'(\w+)\["ad"\]d\(', r'\1.add('),
        (r'(\w+)\["get_full_nam"\]e\(\)', r'get_full_name(\1)'),
        (r'(\w+)\["replac"\]e\(', r'\1.replace('),
        (r'(\w+)\["ge"\]t\(', r'\1.get('),
        (r'(\w+)\["capitalizee"\]\(\)', r'\1.capitalize()'),
        (r'approved_f"{(\w+)\["first_name"\]} {(\w+)\["last_name"\] or ""}"\.strip\(\)', r'f"{get_full_name(\1)}"'),
        (r'rejected_f"{(\w+)\["first_name"\]} {(\w+)\["last_name"\] or ""}"\.strip\(\)', r'f"{get_full_name(\1)}"'),
        (r'target_f"{(\w+)\["first_name"\]} {(\w+)\["last_name"\] or ""}"\.strip\(\)', r'f"{get_full_name(\1)}"'),
        (r'f"{(\w+)\["first_name"\]} {(\w+)\["last_name"\] or ""}"\.strip\(\)', r'get_full_name(\1)'),
        (r'f"{(\w+)\["get_full_nam"\]e\(\)}"', r'get_full_name(\1)'),
        (r'u\["is_admi"\]n\(\)', r'is_admin(u)'),
        (r'u\["is_dispatche"\]r\(\)', r'is_dispatcher(u)'),
        (r'u\["is_technicia"\]n\(\)', r'is_technician(u)'),
        (r'admin_is_admin\((\w+)\)', r'is_admin(\1)'),
    ]
    
    for old, new in specific_replacements:
        fixed_content = re.sub(old, new, fixed_content)
    
    # Записываем исправленное содержимое
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(fixed_content)
    
    print(f"Исправления внесены и сохранены в {output_path}")

if __name__ == "__main__":
    fix_square_brackets("./bot_fixed2.py", "./bot_fixed3.py")