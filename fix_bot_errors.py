#!/usr/bin/env python
"""
Скрипт для автоматического исправления ошибок с f-строками в bot_fixed3.py
"""

import re
import os
import sys

def fix_f_string_errors(input_file, output_file):
    """
    Исправляет ошибки с двойными кавычками внутри f-строк
    
    Args:
        input_file: Путь к исходному файлу
        output_file: Путь к выходному файлу
    """
    print(f"Исправление ошибок f-строк в файле {input_file}")
    
    # Проверяем существование исходного файла
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл {input_file} не найден!")
        return False
    
    try:
        # Читаем исходный файл
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Находим и исправляем все проблемные f-строки
        pattern = r'({template\["[^}]+})'
        
        def replace_double_quotes(match):
            result = match.group(0)
            # Заменяем двойные кавычки на одинарные внутри f-строки
            result = result.replace('["', "[\'")
            result = result.replace('"]', "']")
            return result
        
        fixed_content = re.sub(pattern, replace_double_quotes, content)
        
        # Исправляем также другие случаи с двойными кавычками в f-строках
        # Например: template["title"][:15] -> template['title'][:15]
        fixed_content = fixed_content.replace('template["title"]', "template['title']")
        fixed_content = fixed_content.replace('template["template_id"]', "template['template_id']")
        fixed_content = fixed_content.replace('template["description"]', "template['description']")
        
        # Записываем исправленный контент в выходной файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Исправленный файл сохранен как {output_file}")
        return True
    
    except Exception as e:
        print(f"Ошибка при исправлении файла: {e}")
        return False

def main():
    # Исправляем файл bot_fixed3.py и сохраняем как bot_fixed4.py
    success = fix_f_string_errors('bot_fixed3.py', 'bot_fixed4.py')
    
    if success:
        print("Успешно исправлены ошибки f-строк!")
        
        # Исправляем ссылку в файле start_bot.py
        try:
            with open('start_bot.py', 'r', encoding='utf-8') as f:
                start_bot_content = f.read()
            
            # Заменяем импорт bot_fixed3 на bot_fixed4
            start_bot_content = start_bot_content.replace('from bot_fixed3 import', 'from bot_fixed4 import')
            
            with open('start_bot_fixed.py', 'w', encoding='utf-8') as f:
                f.write(start_bot_content)
            
            print("Успешно создан исправленный файл start_bot_fixed.py")
        except Exception as e:
            print(f"Ошибка при исправлении start_bot.py: {e}")
    else:
        print("Произошла ошибка при исправлении файла.")
        sys.exit(1)

if __name__ == "__main__":
    main()