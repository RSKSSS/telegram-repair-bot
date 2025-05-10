#!/usr/bin/env python3
import re

def fix_telebot_types(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Заменяем все вхождения telebot.types.InlineKeyboardMarkup на InlineKeyboardMarkup
    content = re.sub(r'telebot\.types\.InlineKeyboardMarkup', 'InlineKeyboardMarkup', content)
    
    # Заменяем все вхождения telebot.types.InlineKeyboardButton на InlineKeyboardButton
    content = re.sub(r'telebot\.types\.InlineKeyboardButton', 'InlineKeyboardButton', content)
    
    # Заменяем все вхождения telebot.types.ReplyKeyboardMarkup на ReplyKeyboardMarkup
    content = re.sub(r'telebot\.types\.ReplyKeyboardMarkup', 'ReplyKeyboardMarkup', content)
    
    # Заменяем все вхождения telebot.types.KeyboardButton на KeyboardButton
    content = re.sub(r'telebot\.types\.KeyboardButton', 'KeyboardButton', content)
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"Файл {file_path} успешно обновлен!")

if __name__ == "__main__":
    fix_telebot_types('utils.py')