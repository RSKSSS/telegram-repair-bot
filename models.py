"""
Модели данных для работы с БД
"""
from typing import Dict, Optional
from config import ORDER_STATUSES


class User:
    """
    Модель пользователя в системе
    """
    def __init__(self, user_id: int, first_name: str, last_name: Optional[str] = None,
                 username: Optional[str] = None, role: str = 'technician',
                 is_approved: bool = False, created_at: Optional[str] = None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.role = role
        self.is_approved = is_approved
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Создание объекта User из словаря
        """
        user_id = data.get('user_id')
        first_name = data.get('first_name')
        
        # Проверяем, что обязательные поля не None
        if user_id is None or first_name is None:
            raise ValueError("user_id и first_name не могут быть None")
            
        return cls(
            user_id=user_id,
            first_name=first_name,
            last_name=data.get('last_name'),
            username=data.get('username'),
            role=data.get('role', 'technician'),
            is_approved=data.get('is_approved', False),
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
            'is_approved': self.is_approved,
            'created_at': self.created_at
        }

    def get_full_name(self) -> str:
        """
        Получение полного имени пользователя
        """
        full_name = self.first_name
        if self.last_name:
            full_name += f" {self.last_name}"
        return full_name

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
                 dispatcher_last_name: Optional[str] = None, technicians: Optional[list] = None):
        self.order_id = order_id
        self.client_phone = client_phone
        self.client_name = client_name
        self.client_address = client_address
        self.problem_description = problem_description
        self.dispatcher_id = dispatcher_id
        self.status = status
        self.service_cost = service_cost
        self.service_description = service_description
        self.created_at = created_at
        self.updated_at = updated_at
        self.dispatcher_first_name = dispatcher_first_name
        self.dispatcher_last_name = dispatcher_last_name
        self.technicians = technicians or []

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Создание объекта Order из словаря
        """
        order_id = data.get('order_id')
        client_phone = data.get('client_phone')
        client_name = data.get('client_name')
        client_address = data.get('client_address')
        problem_description = data.get('problem_description')
        
        # Проверяем обязательные поля
        if order_id is None or client_phone is None or client_name is None or client_address is None or problem_description is None:
            raise ValueError("Обязательные поля заказа не могут быть None")
            
        return cls(
            order_id=order_id,
            client_phone=client_phone,
            client_name=client_name,
            client_address=client_address,
            problem_description=problem_description,
            dispatcher_id=data.get('dispatcher_id'),
            status=data.get('status', 'new'),
            service_cost=data.get('service_cost'),
            service_description=data.get('service_description'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            dispatcher_first_name=data.get('dispatcher_first_name'),
            dispatcher_last_name=data.get('dispatcher_last_name'),
            technicians=data.get('technicians', [])
        )

    def to_dict(self) -> Dict:
        """
        Конвертация объекта Order в словарь
        """
        return {
            'order_id': self.order_id,
            'client_phone': self.client_phone,
            'client_name': self.client_name,
            'client_address': self.client_address,
            'problem_description': self.problem_description,
            'dispatcher_id': self.dispatcher_id,
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
        result = (
            f"📝 *Заказ #{self.order_id}*\n\n"
            f"🔄 Статус: *{self.status_to_russian()}*\n"
            f"📱 Телефон клиента: {self.client_phone}\n"
            f"👤 Имя клиента: {self.client_name}\n"
            f"🏠 Адрес: {self.client_address}\n"
            f"🔧 Проблема: {self.problem_description}\n"
        )

        # Добавляем информацию о диспетчере
        if self.dispatcher_first_name:
            dispatcher_name = self.dispatcher_first_name
            if self.dispatcher_last_name:
                dispatcher_name += f" {self.dispatcher_last_name}"
            result += f"📞 Диспетчер: {dispatcher_name}\n"

        # Добавляем информацию о техниках
        if self.technicians:
            techs = []
            for tech in self.technicians:
                tech_name = tech['first_name']
                if tech['last_name']:
                    tech_name += f" {tech['last_name']}"
                techs.append(tech_name)
            result += f"👨‍🔧 Назначенные техники: {', '.join(techs)}\n"

        # Добавляем информацию о стоимости услуг
        if self.service_cost is not None:
            result += f"💰 Стоимость: {self.service_cost} руб.\n"

        # Добавляем информацию о выполненных работах
        if self.service_description:
            result += f"📋 Описание работ: {self.service_description}\n"

        # Добавляем информацию о дате создания и обновления
        if self.created_at:
            result += f"📅 Создан: {self.created_at}\n"
        if self.updated_at:
            result += f"🔄 Обновлен: {self.updated_at}\n"

        return result

    def status_to_russian(self) -> str:
        """
        Преобразование статуса заказа в читаемый вид на русском языке
        """
        return ORDER_STATUSES.get(self.status, self.status)


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
        assignment_id = data.get('assignment_id')
        order_id = data.get('order_id')
        technician_id = data.get('technician_id')
        assigned_by = data.get('assigned_by')
        
        # Проверяем обязательные поля
        if assignment_id is None or order_id is None or technician_id is None or assigned_by is None:
            raise ValueError("Обязательные поля назначения не могут быть None")
        
        return cls(
            assignment_id=assignment_id,
            order_id=order_id,
            technician_id=technician_id,
            assigned_by=assigned_by,
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
        name = self.first_name or ""
        if self.last_name:
            name += f" {self.last_name}"
        return name