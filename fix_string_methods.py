#!/usr/bin/env python3
"""
Скрипт для исправления ошибок в методах строк
в файле bot_fixed.py
"""
import re

def fix_string_methods(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Замена неправильных методов строк на правильные
    content = content.replace('callback_data["startswit"]h', 'callback_data.startswith')
    content = content.replace('callback_data["spli"]t', 'callback_data.split')
    content = content.replace('["capitaliz"]', '.capitalize')
    content = content.replace('["appen"]', '.append')
    content = content.replace('["startswit"]h', '.startswith')
    
    # Записываем результат в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    fix_string_methods('bot_fixed.py', 'bot_fixed2.py')