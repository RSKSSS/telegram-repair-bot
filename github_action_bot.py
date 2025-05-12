"""
Специальная версия бота для запуска через GitHub Actions.
GitHub Actions запускает скрипт каждые 5 минут, поэтому бот не должен работать в режиме polling.
Вместо этого он обрабатывает последние обновления и завершается.
"""
import os
import sys
import logging
import traceback
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_action_bot')

# Проверка наличия токена бота
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

try:
    import telebot
    from telebot import types
    
    # Создаем экземпляр бота
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    
    # Получаем ID последнего обновления из файла (если он есть)
    last_update_id = 0
    try:
        with open('last_update_id.txt', 'r') as f:
            last_update_id = int(f.read().strip())
            logger.info(f"Загружен last_update_id: {last_update_id}")
    except Exception as e:
        logger.info(f"Не удалось загрузить last_update_id: {e}")
    
    # Получаем обновления (начиная с последнего известного ID + 1)
    logger.info(f"Получение обновлений, начиная с ID: {last_update_id + 1}")
    updates = bot.get_updates(offset=last_update_id + 1, timeout=1)
    
    if updates:
        logger.info(f"Получено {len(updates)} обновлений")
        
        # Обрабатываем каждое обновление
        for update in updates:
            try:
                # Обработка сообщений
                if update.message:
                    # Простой пример - эхо-бот
                    bot.send_message(update.message.chat.id, 
                                    f"Получено сообщение: {update.message.text}")
                    
                # Тут можно добавить более сложную логику обработки
                # например:
                # - Проверить, есть ли команда /start и обработать её
                # - Проверить состояние пользователя и выполнить соответствующее действие
                
                # Сохраняем ID последнего обновления
                last_update_id = update.update_id
                
            except Exception as e:
                logger.error(f"Ошибка при обработке обновления: {e}")
                logger.error(traceback.format_exc())
        
        # Сохраняем ID последнего обновления в файл
        try:
            with open('last_update_id.txt', 'w') as f:
                f.write(str(last_update_id))
                logger.info(f"Сохранен last_update_id: {last_update_id}")
        except Exception as e:
            logger.error(f"Не удалось сохранить last_update_id: {e}")
    
    else:
        logger.info("Новых обновлений не получено")
    
    # Отправляем информацию о работе системы
    try:
        # Отправляем статус раз в час (чтобы не спамить)
        current_hour = datetime.now().hour
        if current_hour % 4 == 0 and datetime.now().minute < 10:
            # Получаем ID администраторов (замените на свою логику)
            admin_ids = [123456789]  # Замените на реальные ID админов
            
            for admin_id in admin_ids:
                try:
                    message = (
                        f"🤖 *Статус бота через GitHub Actions*\n\n"
                        f"⏰ Время проверки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                        f"📊 Последний обработанный update_id: {last_update_id}\n"
                        f"✅ Статус: Работает"
                    )
                    bot.send_message(admin_id, message, parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Ошибка при отправке статуса админу {admin_id}: {e}")
    
    except Exception as e:
        logger.error(f"Ошибка при отправке статуса: {e}")
    
except Exception as e:
    logger.error(f"Критическая ошибка: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)