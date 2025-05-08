#!/usr/bin/env python3
"""
Скрипт для тестирования процесса создания и обработки заказа
"""
import sys
from database import initialize_database, save_user, approve_user, update_user_role
from database import save_order, assign_order, update_order, get_order

def main():
    # Инициализация БД
    initialize_database()
    
    print('\n--- Создание тестовых пользователей ---')
    
    # Создаем тестового админа
    admin_id = 1001
    admin = save_user(admin_id, 'Админ', 'Админович', 'admin_user', role='admin', is_approved=True)
    print(f'Создан админ: {admin_id}')
    
    # Создаем тестового диспетчера
    dispatcher_id = 1002
    dispatcher = save_user(dispatcher_id, 'Диспетчер', 'Диспетчеров', 'dispatcher_user', role='dispatcher', is_approved=True)
    print(f'Создан диспетчер: {dispatcher_id}')
    
    # Создаем тестового мастера
    technician_id = 1003
    technician = save_user(technician_id, 'Мастер', 'Мастеров', 'technician_user', role='technician', is_approved=True)
    print(f'Создан мастер: {technician_id}')
    
    print('\n--- Создание тестового заказа ---')
    
    # Создаем заказ от имени диспетчера
    client_phone = '+79001234567'
    client_name = 'Иван Клиентов'
    client_address = 'г. Москва, ул. Примерная, д. 123'
    problem_description = 'Не включается компьютер, нужна диагностика'
    
    order_id = save_order(dispatcher_id, client_phone, client_name, client_address, problem_description)
    print(f'Создан заказ #{order_id}')
    
    print('\n--- Назначение мастера на заказ ---')
    
    # Назначаем мастера на заказ
    assignment_id = assign_order(order_id, technician_id, admin_id)
    print(f'Мастер назначен на заказ, ID назначения: {assignment_id}')
    
    print('\n--- Изменение статуса заказа на "в работе" ---')
    
    # Меняем статус заказа на "в работе"
    update_order(order_id, status='in_progress')
    order = get_order(order_id)
    print(f'Статус заказа: {order.status}')
    
    print('\n--- Завершение заказа с указанием стоимости 15$ ---')
    
    # Завершаем заказ и указываем стоимость 15$
    update_order(order_id, status='completed', service_cost=15, 
                service_description='Заменен блок питания, устранены проблемы с загрузкой Windows')
    order = get_order(order_id)
    print(f'Статус заказа: {order.status}')
    print(f'Стоимость услуг: ${order.service_cost}')
    print(f'Описание услуг: {order.service_description}')
    
    print('\n--- Детали заказа ---')
    print(order.format_for_display(user_role='admin'))
    
if __name__ == '__main__':
    main()