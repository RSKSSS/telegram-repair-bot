#!/usr/bin/env python3
"""
Скрипт для автоматической замены обращений к атрибутам на обращения к элементам словаря
в файле bot.py
"""
import re

def fix_attribute_access(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Для начала заменим проблемные вызовы методов
    replacements = [
        ('user.is_admin()', 'is_admin(user)'),
        ('user.is_dispatcher()', 'is_dispatcher(user)'),
        ('user.is_technician()', 'is_technician(user)'),
        ('order.format_for_display', 'format_orders_list([order])'),
        ('user.get_full_name()', 'f"{user[\"first_name\"]} {user[\"last_name\"] or \"\"}".strip()'),
        ('status_to_russian', 'ORDER_STATUSES.get'),
        ('order["format_for_display"]', 'format_orders_list([order])'),
        ('user["is_admin"]()', 'is_admin(user)'),
        ('user["is_dispatcher"]()', 'is_dispatcher(user)'),
        ('user["is_technician"]()', 'is_technician(user)'),
        ('user["get_full_name"]()', 'f"{user[\"first_name\"]} {user[\"last_name\"] or \"\"}".strip()'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Замена обращений к атрибутам на обращения к элементам словаря
    # Паттерн для замены user.attribute на user["attribute"]
    pattern1 = r'(\w+)\.(\w+)(?!\()'
    # Исключаем некоторые случаи, когда это может быть не обращение к атрибуту объекта
    exclude_prefixes = ['bot.', 'message.', 'call.', 'os.', 'cursor.', 'conn.', 're.', 'logger.', 'telebot.', 'keyboard.', 'markup.']
    common_method_names = ['format', 'join', 'strip', 'replace', 'lower', 'upper', 'append', 'extend', 'pop', 'sort', 'copy', 'find', 'update', 'fetchall', 'fetchone', 'execute', 'commit', 'close']
    
    def replace_attribute(match):
        full_match = match.group(0)
        obj_name = match.group(1)
        attr_name = match.group(2)
        
        # Исключаем некоторые специальные случаи
        for prefix in exclude_prefixes:
            if full_match.startswith(prefix):
                return full_match
        
        # Исключаем распространенные методы
        if attr_name in common_method_names:
            return full_match
            
        return f'{obj_name}["{attr_name}"]'
    
    # Замена паттернов
    modified_content = re.sub(pattern1, replace_attribute, content)
    
    # Ищем и заменяем вызовы методов у объекта, который уже был преобразован в словарь
    pattern2 = r'(\w+)\["(\w+)"\]\(\)'
    
    def replace_method_call(match):
        obj_name = match.group(1)
        method_name = match.group(2)
        
        if method_name == 'is_admin':
            return f'is_admin({obj_name})'
        elif method_name == 'is_dispatcher':
            return f'is_dispatcher({obj_name})'
        elif method_name == 'is_technician':
            return f'is_technician({obj_name})'
        elif method_name == 'get_full_name':
            return f'f"{{{obj_name}[\\"first_name\\"]}} {{{obj_name}[\\"last_name\\"] or \\"\\"}}".strip()'
        else:
            return f'{obj_name}["{method_name}"]'
    
    modified_content = re.sub(pattern2, replace_method_call, modified_content)
    
    # Записываем результат в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

if __name__ == '__main__':
    fix_attribute_access('bot.py', 'bot_fixed.py')