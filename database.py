import logging
from datetime import datetime
from app import db
from models import User, Order

logger = logging.getLogger(__name__)

def initialize_database():
    """Create the necessary tables if they don't exist"""
    logger.info("Initializing database...")
    
    # This function is not needed with Flask-SQLAlchemy
    # Tables are created automatically with db.create_all() in app.py
    
    logger.info("Database initialized successfully")

def save_user(user_id, first_name, last_name=None, username=None, role='client'):
    """Save user information to the database"""
    # Check if user exists
    user = User.query.filter_by(user_id=user_id).first()
    
    if user:
        # Update existing user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
    else:
        # Create new user
        user = User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            role=role
        )
        db.session.add(user)
    
    db.session.commit()
    return user_id

def get_user(user_id):
    """Get user information from the database"""
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        return user.to_dict()
    return None

def get_user_role(user_id):
    """Get user role from the database"""
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        return user.role
    return 'client'  # Default role

def get_all_users():
    """Get all users from the database"""
    users = User.query.order_by(User.role.desc(), User.user_id.asc()).all()
    return [user.to_dict() for user in users]

def update_user_role(user_id, role):
    """Update user role in the database"""
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user.role = role
        db.session.commit()
        return True
    return False

def save_order(user_id, client_phone, client_name, client_address, problem_description):
    """Save an order to the database"""
    # Create new order
    order = Order(
        user_id=user_id,
        client_phone=client_phone,
        client_name=client_name,
        client_address=client_address,
        problem_description=problem_description,
        status='new'
    )
    
    db.session.add(order)
    db.session.commit()
    
    return order.id

def update_order(order_id, status=None, service_cost=None, service_description=None):
    """Update an order in the database"""
    order = Order.query.get(order_id)
    
    if order:
        if status is not None:
            order.status = status
        
        if service_cost is not None:
            order.service_cost = service_cost
        
        if service_description is not None:
            order.service_description = service_description
        
        # updated_at will be automatically set by the onupdate trigger
        db.session.commit()
        return True
    
    return False

def get_order(order_id):
    """Get an order from the database"""
    order = Order.query.get(order_id)
    if order:
        return order.to_dict()
    return None

def get_orders_by_user(user_id):
    """Get all orders by a specific user"""
    # Custom ordering based on status
    orders = Order.query.filter_by(user_id=user_id).order_by(
        db.case(
            [
                (Order.status == 'new', 1),
                (Order.status == 'processing', 2),
                (Order.status == 'completed', 3),
                (Order.status == 'cancelled', 4)
            ],
            else_=5
        ),
        Order.created_at.desc()
    ).all()
    
    return [order.to_dict() for order in orders]

def get_orders_by_phone(phone):
    """Get all orders by a client phone number"""
    orders = Order.query.filter_by(client_phone=phone).order_by(Order.created_at.desc()).all()
    return [order.to_dict() for order in orders]

def get_all_orders(status=None):
    """Get all orders from the database"""
    if status:
        orders = Order.query.filter_by(status=status).order_by(Order.created_at.desc()).all()
    else:
        # Custom ordering based on status
        orders = Order.query.order_by(
            db.case(
                [
                    (Order.status == 'new', 1),
                    (Order.status == 'processing', 2),
                    (Order.status == 'completed', 3),
                    (Order.status == 'cancelled', 4)
                ],
                else_=5
            ),
            Order.created_at.desc()
        ).all()
    
    return [order.to_dict() for order in orders]
