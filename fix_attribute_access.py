#!/usr/bin/env python3
"""
Скрипт для автоматической замены обращений к атрибутам на обращения к элементам словаря
в файле bot.py
"""
import re

def fix_attribute_access(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Замена обращений к атрибутам на обращения к элементам словаря
    # Паттерн для замены user.attribute на user["attribute"]
    pattern1 = r'(\w+)\.(\w+)'
    # Исключаем некоторые случаи, когда это может быть не обращение к атрибуту объекта
    exclude_prefixes = ['bot.', 'message.', 'call.', 'os.', 'cursor.', 'conn.', 're.', 'logger.', 'telebot.']
    
    def replace_attribute(match):
        full_match = match.group(0)
        obj_name = match.group(1)
        attr_name = match.group(2)
        
        # Исключаем некоторые специальные случаи
        for prefix in exclude_prefixes:
            if full_match.startswith(prefix):
                return full_match
        
        # Исключаем вызовы методов (например, user.is_admin())
        if '(' in attr_name or attr_name in ['format', 'join', 'strip', 'replace', 'lower', 'upper', 'append', 'extend', 'pop', 'sort', 'copy', 'find', 'update']:
            return full_match
            
        return f'{obj_name}["{attr_name}"]'
    
    # Замена паттернов
    modified_content = re.sub(pattern1, replace_attribute, content)
    
    # Замена вызовов методов на обращения к функциям из utils
    modified_content = modified_content.replace('user.is_admin()', 'is_admin(user)')
    modified_content = modified_content.replace('user.is_dispatcher()', 'is_dispatcher(user)')
    modified_content = modified_content.replace('user.is_technician()', 'is_technician(user)')
    modified_content = modified_content.replace('order.format_for_display', 'format_orders_list([order])')
    modified_content = modified_content.replace('user.get_full_name()', f'f"{{user[\\"first_name\\"]}} {{user[\\"last_name\\"] or \\"\\"}}".strip()')
    
    # Замена вызовов других методов на их эквиваленты или заглушки
    modified_content = modified_content.replace('user.status_to_russian', 'ORDER_STATUSES.get')

    # Записываем результат в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

if __name__ == '__main__':
    fix_attribute_access('bot.py', 'bot_fixed.py')