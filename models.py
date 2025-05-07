from datetime import datetime
from typing import Optional, Dict, Any
from app import db

class User(db.Model):
    """User model for the database"""
    __tablename__ = 'users'
    
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    role = db.Column(db.String(20), nullable=False, default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.user_id}: {self.first_name}>'
    
    @classmethod
    def from_dict(cls, data):
        """Create a User instance from dictionary data"""
        user = cls(
            user_id=data['user_id'],
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            username=data.get('username'),
            role=data.get('role', 'client')
        )
        return user
    
    def to_dict(self):
        """Convert User to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Order(db.Model):
    """Order model for the database"""
    __tablename__ = 'orders'
    
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_address = db.Column(db.String(255), nullable=False)
    problem_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='new')
    service_cost = db.Column(db.Float)
    service_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Order {self.id}: {self.status}>'
    
    @classmethod
    def from_dict(cls, data):
        """Create an Order instance from dictionary data"""
        order = cls(
            user_id=data['user_id'],
            client_phone=data['client_phone'],
            client_name=data['client_name'],
            client_address=data['client_address'],
            problem_description=data['problem_description'],
            status=data.get('status', 'new'),
            service_cost=data.get('service_cost'),
            service_description=data.get('service_description')
        )
        return order
    
    def to_dict(self):
        """Convert Order to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'client_phone': self.client_phone,
            'client_name': self.client_name,
            'client_address': self.client_address,
            'problem_description': self.problem_description,
            'status': self.status,
            'service_cost': self.service_cost,
            'service_description': self.service_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def format_for_display(self):
        """Format the order for display to users"""
        status_emoji = {
            'new': '🆕',
            'processing': '⚙️',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        order_text = f"📋 <b>Заказ #{self.id}</b>\n"
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
            created_at_str = self.created_at.strftime("%Y-%m-%d %H:%M")
            order_text += f"\n📅 <b>Создан:</b> {created_at_str}\n"
        
        return order_text
    
    def status_to_russian(self):
        """Convert status to Russian language"""
        status_map = {
            'new': 'Новый',
            'processing': 'В работе',
            'completed': 'Завершен',
            'cancelled': 'Отменен'
        }
        return status_map.get(self.status, self.status)
