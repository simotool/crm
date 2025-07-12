from . import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    order_source = db.Column(db.String(50), nullable=False)  # Google Sheet, Webhook
    order_status = db.Column(db.String(50), nullable=False, default='قيد الانتظار')
    # حالات الطلب: قيد الانتظار، اتصال أول، اتصال ثانٍ، مؤكد، ملغى، تم الشحن، تم التسليم، مرتجع
    confirmation_staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=True)
    delivery_company_id = db.Column(db.Integer, db.ForeignKey('delivery_companies.company_id'), nullable=True)
    delivery_price = db.Column(db.Float, nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    shipping_tracking_id = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text)
    
    # تواريخ مهمة
    first_call_date = db.Column(db.DateTime, nullable=True)
    second_call_date = db.Column(db.DateTime, nullable=True)
    confirmed_date = db.Column(db.DateTime, nullable=True)
    shipped_date = db.Column(db.DateTime, nullable=True)
    delivered_date = db.Column(db.DateTime, nullable=True)
    cancelled_date = db.Column(db.DateTime, nullable=True)
    returned_date = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='order', lazy=True)
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_address': self.customer_address,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'order_source': self.order_source,
            'order_status': self.order_status,
            'confirmation_staff_id': self.confirmation_staff_id,
            'delivery_company_id': self.delivery_company_id,
            'delivery_price': self.delivery_price,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'shipping_tracking_id': self.shipping_tracking_id,
            'notes': self.notes,
            'first_call_date': self.first_call_date.isoformat() if self.first_call_date else None,
            'second_call_date': self.second_call_date.isoformat() if self.second_call_date else None,
            'confirmed_date': self.confirmed_date.isoformat() if self.confirmed_date else None,
            'shipped_date': self.shipped_date.isoformat() if self.shipped_date else None,
            'delivered_date': self.delivered_date.isoformat() if self.delivered_date else None,
            'cancelled_date': self.cancelled_date.isoformat() if self.cancelled_date else None,
            'returned_date': self.returned_date.isoformat() if self.returned_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_profit(self):
        """حساب ربح الطلب"""
        if not self.product or self.order_status not in ['تم التسليم']:
            return 0
        
        # إجمالي الإيرادات
        total_revenue = self.product.price * self.quantity
        
        # إجمالي المصاريف المرتبطة بهذا الطلب
        order_expenses = sum([expense.amount for expense in self.expenses])
        
        # تكلفة التوصيل
        delivery_cost = self.delivery_price or 0
        
        # الربح = الإيرادات - المصاريف - تكلفة التوصيل
        profit = total_revenue - order_expenses - delivery_cost
        
        return profit
    
    def __repr__(self):
        return f'<Order {self.order_id}: {self.customer_name}>'

