"""
Файл для запуска Telegram бота и простого веб-сервера на Render
"""
import os
import sys
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('render_server')

# Определяем порт из переменной окружения Render или используем порт по умолчанию
PORT = int(os.environ.get('PORT', 10000))

# Простой обработчик HTTP-запросов
class BotStatusHandler(BaseHTTPRequestHandler):
    """Простой обработчик HTTP запросов для статуса бота"""
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Устанавливает заголовки ответа"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def do_GET(self):
        """Обрабатывает GET запросы"""
        if self.path == '/':
            # Основная страница с информацией о статусе
            self._set_headers()
            response = {
                'status': 'running',
                'service': 'telegram_bot',
                'uptime': get_uptime(),
                'message': 'Бот работает в режиме polling'
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/health':
            # Эндпоинт для проверки работоспособности
            self._set_headers()
            response = {'status': 'ok'}
            self.wfile.write(json.dumps(response).encode())
        else:
            # Неизвестный путь
            self._set_headers(404)
            response = {'error': 'Not Found'}
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Переопределяем логирование, чтобы использовать наш логгер"""
        logger.info("%s - %s" % (self.address_string(), format % args))

# Переменная для хранения времени запуска
start_time = None

def get_uptime():
    """Возвращает время работы сервера в секундах"""
    import time
    global start_time
    if start_time is None:
        return 0
    return int(time.time() - start_time)

def run_http_server():
    """Запускает HTTP сервер"""
    import time
    global start_time
    start_time = time.time()
    
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, BotStatusHandler)
    logger.info(f'Запуск HTTP сервера на порту {PORT}...')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Получен сигнал завершения, останавливаем HTTP сервер...')
        httpd.server_close()
    except Exception as e:
        logger.error(f'Ошибка HTTP сервера: {e}')
        logger.error(traceback.format_exc())

def run_telegram_bot():
    """Запускает Telegram бот через render_bot.py"""
    logger.info('Запуск Telegram бота...')
    
    # Проверяем, не запущен ли уже бот с этим токеном
    import time
    import requests
    import os
    import json
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error('TELEGRAM_BOT_TOKEN не найден в переменных окружения! Бот не будет запущен.')
        return
    
    # Сначала проверяем, можем ли мы получить обновления - если нет, значит, другой экземпляр уже работает
    try:
        # Пробуем сбросить webhook, если он был установлен
        logger.info('Сброс webhook перед запуском бота...')
        requests.get(f'https://api.telegram.org/bot{token}/deleteWebhook')
        time.sleep(5)  # Ждем немного, чтобы изменения вступили в силу
        
        # Проверяем, освободился ли webhook
        webhook_info = requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo').json()
        if webhook_info.get('result', {}).get('url'):
            logger.warning(f'Webhook не удалось сбросить, он все еще установлен на {webhook_info["result"]["url"]}')
            logger.info('Повторная попытка сброса webhook и ожидание 30 секунд...')
            requests.get(f'https://api.telegram.org/bot{token}/deleteWebhook')
            time.sleep(30)  # Ждем дольше
    except Exception as e:
        logger.error(f'Ошибка при проверке/сбросе webhook: {e}')
    
    # Добавляем задержку перед запуском, чтобы предыдущие экземпляры освободили соединение
    logger.info('Ожидание 10 секунд перед запуском бота...')
    time.sleep(10)
    
    # Запускаем бота с вложенными обработчиками ошибок
    try:
        # Пробуем запустить бота с обработкой ошибок из модуля single_instance_bot
        logger.info('Запуск бота через single_instance_bot...')
        # Импортируем модуль, но реальный запуск делаем через working_bot
        import single_instance_bot
        
        try:
            # Напрямую запускаем через working_bot
            logger.info('Запуск бота через working_bot.start_bot_polling...')
            from working_bot import start_bot_polling
            start_bot_polling()
        except Exception as e:
            logger.error(f'Ошибка при запуске бота через working_bot: {e}')
            logger.error(traceback.format_exc())
            
            # Пробуем альтернативные методы запуска
            try:
                # Запускаем бота через render_bot.py
                logger.info('Попытка запуска через render_bot.py...')
                from render_bot import main as start_bot
                start_bot()
            except ImportError:
                logger.error('Не удалось импортировать render_bot.py, все способы запуска исчерпаны')
            except Exception as e:
                logger.error(f'Ошибка при запуске бота через render_bot: {e}')
                logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f'Критическая ошибка при запуске бота: {e}')
        logger.error(traceback.format_exc())

def main():
    """Основная функция для запуска бота и веб-сервера в разных потоках"""
    try:
        # Запускаем HTTP сервер в отдельном потоке
        http_thread = threading.Thread(target=run_http_server)
        http_thread.daemon = True  # Поток завершится, когда завершится основной
        http_thread.start()
        
        # Запускаем бота в главном потоке
        run_telegram_bot()
        
    except Exception as e:
        logger.error(f'Критическая ошибка: {e}')
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()