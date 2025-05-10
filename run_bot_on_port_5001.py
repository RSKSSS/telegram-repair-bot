#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота на отдельном порту для избежания конфликтов с Flask
"""

import os
import sys
import subprocess
import signal
import time

def run_bot():
    """Запускает минимальную версию бота в отдельном процессе"""
    print("Запуск минимальной версии Telegram бота...")
    
    try:
        # Устанавливаем переменную окружения PORT для использования порта 5001
        env = os.environ.copy()
        env["PORT"] = "5001"  # Используем другой порт
        
        # Запускаем бота в отдельном процессе
        bot_process = subprocess.Popen([sys.executable, "minimal_bot.py"], env=env)
        
        print(f"Бот запущен с PID: {bot_process.pid}")
        
        # Регистрируем обработчик сигнала для корректного завершения
        def signal_handler(sig, frame):
            print(f"Получен сигнал {sig}, завершаем работу бота...")
            bot_process.terminate()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Ждем завершения процесса бота
        bot_process.wait()
        
        return bot_process.returncode
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_bot()
    sys.exit(exit_code)