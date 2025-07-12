from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models
from .user import User
from .product import Product
from .delivery_company import DeliveryCompany
from .staff import Staff
from .delivery_price_list import DeliveryPriceList
from .expense import Expense
from .order import Order

__all__ = [
    'db',
    'User',
    'Product', 
    'DeliveryCompany',
    'Staff',
    'DeliveryPriceList',
    'Expense',
    'Order'
]

