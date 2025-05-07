import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create the base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///computer_repair.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with SQLAlchemy
db.init_app(app)

# Import models after db initialization to avoid circular imports
from models import Order, User

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/orders')
def orders():
    """List all orders route"""
    all_orders = Order.query.all()
    return render_template('orders.html', orders=all_orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    """Order detail route"""
    order = Order.query.get_or_404(order_id)
    return render_template('order_detail.html', order=order)

@app.route('/api/orders')
def api_orders():
    """API route to get all orders as JSON"""
    orders = Order.query.all()
    return jsonify([order.to_dict() for order in orders])

# Create tables when app starts if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)