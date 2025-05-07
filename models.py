from typing import Optional, List, Dict
from datetime import datetime


class User:
    """
    Модель пользователя в системе
    """
    def __init__(self, user_id: int, first_name: str, last_name: Optional[str] = None,
                 username: Optional[str] = None, role: str = 'technician',
                 created_at: Optional[str] = None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.role = role
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Создание объекта User из словаря
        """
        if not data:
            return None
            
        return cls(
            user_id=data['user_id'],
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            username=data.get('username'),
            role=data.get('role', 'technician'),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> Dict:
        """
        Конвертация объекта User в словарь
        """
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at
        }

    def get_full_name(self) -> str:
        """
        Получение полного имени пользователя
        """
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    def is_admin(self) -> bool:
        """
        Проверка, является ли пользователь администратором
        """
        return self.role == 'admin'
    
    def is_dispatcher(self) -> bool:
        """
        Проверка, является ли пользователь диспетчером
        """
        return self.role == 'dispatcher'
    
    def is_technician(self) -> bool:
        """
        Проверка, является ли пользователь техником
        """
        return self.role == 'technician'


class Order:
    """
    Модель заказа в системе
    """
    def __init__(self, order_id: int, client_phone: str, client_name: str,
                 client_address: str, problem_description: str, dispatcher_id: Optional[int] = None,
                 status: str = 'new', service_cost: Optional[float] = None,
                 service_description: Optional[str] = None, created_at: Optional[str] = None,
                 updated_at: Optional[str] = None, dispatcher_first_name: Optional[str] = None,
                 dispatcher_last_name: Optional[str] = None):
        self.order_id = order_id
        self.dispatcher_id = dispatcher_id
        self.client_phone = client_phone
        self.client_name = client_name
        self.client_address = client_address
        self.problem_description = problem_description
        self.status = status
        self.service_cost = service_cost
        self.service_description = service_description
        self.created_at = created_at
        self.updated_at = updated_at
        self.dispatcher_first_name = dispatcher_first_name
        self.dispatcher_last_name = dispatcher_last_name
        self.technicians = []

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Создание объекта Order из словаря
        """
        if not data:
            return None
            
        order = cls(
            order_id=data['order_id'],
            dispatcher_id=data.get('dispatcher_id'),
            client_phone=data['client_phone'],
            client_name=data['client_name'],
            client_address=data['client_address'],
            problem_description=data['problem_description'],
            status=data.get('status', 'new'),
            service_cost=data.get('service_cost'),
            service_description=data.get('service_description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            dispatcher_first_name=data.get('dispatcher_first_name'),
            dispatcher_last_name=data.get('dispatcher_last_name')
        )
        
        # Добавляем техников, если они есть
        if 'technicians' in data:
            order.technicians = data['technicians']
            
        return order

    def to_dict(self) -> Dict:
        """
        Конвертация объекта Order в словарь
        """
        return {
            'order_id': self.order_id,
            'dispatcher_id': self.dispatcher_id,
            'client_phone': self.client_phone,
            'client_name': self.client_name,
            'client_address': self.client_address,
            'problem_description': self.problem_description,
            'status': self.status,
            'service_cost': self.service_cost,
            'service_description': self.service_description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'dispatcher_first_name': self.dispatcher_first_name,
            'dispatcher_last_name': self.dispatcher_last_name,
            'technicians': self.technicians
        }

    def format_for_display(self) -> str:
        """
        Форматирование заказа для отображения пользователям
        """
        created_at = self.created_at.strftime('%d.%m.%Y %H:%M') if isinstance(self.created_at, datetime) else self.created_at
        
        order_text = (
            f"📋 *Заказ №{self.order_id}*\n\n"
            f"📱 *Телефон:* {self.client_phone}\n"
            f"👤 *Клиент:* {self.client_name}\n"
            f"🏠 *Адрес:* {self.client_address}\n"
            f"🔧 *Проблема:* {self.problem_description}\n"
            f"🔄 *Статус:* {self.status_to_russian()}\n"
        )
        
        if self.service_cost:
            order_text += f"💰 *Стоимость:* {self.service_cost} руб.\n"
            
        if self.service_description:
            order_text += f"📝 *Описание работ:* {self.service_description}\n"
            
        if created_at:
            order_text += f"⏱ *Создан:* {created_at}\n"
            
        if self.dispatcher_first_name:
            dispatcher_name = f"{self.dispatcher_first_name}"
            if self.dispatcher_last_name:
                dispatcher_name += f" {self.dispatcher_last_name}"
            order_text += f"📞 *Диспетчер:* {dispatcher_name}\n"
            
        if self.technicians:
            techs = []
            for tech in self.technicians:
                tech_name = tech['first_name']
                if tech.get('last_name'):
                    tech_name += f" {tech['last_name']}"
                techs.append(tech_name)
            order_text += f"👨‍🔧 *Назначен:* {', '.join(techs)}\n"
            
        return order_text

    def status_to_russian(self) -> str:
        """
        Преобразование статуса заказа в читаемый вид на русском языке
        """
        status_map = {
            'new': 'Новый',
            'assigned': 'Назначен',
            'in_progress': 'В работе',
            'completed': 'Завершен',
            'cancelled': 'Отменен'
        }
        return status_map.get(self.status, self.status)


class Assignment:
    """
    Модель назначения заказа технику
    """
    def __init__(self, assignment_id: int, order_id: int, technician_id: int,
                 assigned_by: int, assigned_at: Optional[str] = None,
                 first_name: Optional[str] = None, last_name: Optional[str] = None,
                 username: Optional[str] = None):
        self.assignment_id = assignment_id
        self.order_id = order_id
        self.technician_id = technician_id
        self.assigned_by = assigned_by
        self.assigned_at = assigned_at
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Создание объекта Assignment из словаря
        """
        if not data:
            return None
            
        return cls(
            assignment_id=data['assignment_id'],
            order_id=data['order_id'],
            technician_id=data['technician_id'],
            assigned_by=data['assigned_by'],
            assigned_at=data.get('assigned_at'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            username=data.get('username')
        )

    def to_dict(self) -> Dict:
        """
        Конвертация объекта Assignment в словарь
        """
        return {
            'assignment_id': self.assignment_id,
            'order_id': self.order_id,
            'technician_id': self.technician_id,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username
        }

    def get_technician_name(self) -> str:
        """
        Получение имени техника
        """
        if self.first_name:
            if self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.first_name
        return f"ID: {self.technician_id}"