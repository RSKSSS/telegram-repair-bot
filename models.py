from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import json

@dataclass
class User:
    user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    role: str = 'client'
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data['user_id'],
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            username=data.get('username'),
            role=data.get('role', 'client')
        )
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'role': self.role
        }

@dataclass
class Order:
    order_id: int
    user_id: int
    client_phone: str
    client_name: str
    client_address: str
    problem_description: str
    status: str = 'new'
    service_cost: Optional[float] = None
    service_description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            order_id=data['order_id'],
            user_id=data['user_id'],
            client_phone=data['client_phone'],
            client_name=data['client_name'],
            client_address=data['client_address'],
            problem_description=data['problem_description'],
            status=data.get('status', 'new'),
            service_cost=data.get('service_cost'),
            service_description=data.get('service_description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'client_phone': self.client_phone,
            'client_name': self.client_name,
            'client_address': self.client_address,
            'problem_description': self.problem_description,
            'status': self.status,
            'service_cost': self.service_cost,
            'service_description': self.service_description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def format_for_display(self):
        """Format the order for display to users"""
        status_emoji = {
            'new': '🆕',
            'processing': '⚙️',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        order_text = f"📋 <b>Заказ #{self.order_id}</b>\n"
        order_text += f"{status_emoji.get(self.status, '❓')} <b>Статус:</b> {self.status_to_russian()}\n\n"
        order_text += f"👤 <b>Клиент:</b> {self.client_name}\n"
        order_text += f"📞 <b>Телефон:</b> {self.client_phone}\n"
        order_text += f"🏠 <b>Адрес:</b> {self.client_address}\n\n"
        order_text += f"🔧 <b>Проблема:</b>\n{self.problem_description}\n"
        
        if self.service_description:
            order_text += f"\n🛠 <b>Выполненные работы:</b>\n{self.service_description}\n"
        
        if self.service_cost:
            order_text += f"\n💰 <b>Стоимость:</b> {self.service_cost} руб.\n"
        
        if self.created_at:
            order_text += f"\n📅 <b>Создан:</b> {self.created_at}\n"
        
        return order_text
    
    def status_to_russian(self):
        status_map = {
            'new': 'Новый',
            'processing': 'В работе',
            'completed': 'Завершен',
            'cancelled': 'Отменен'
        }
        return status_map.get(self.status, self.status)
