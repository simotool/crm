from . import db
from datetime import datetime

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    expense_id = db.Column(db.Integer, primary_key=True)
    expense_type = db.Column(db.String(100), nullable=False)  # إعلانات، عمال تأكيد، تغليف، ثابتة، إرجاع
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    description = db.Column(db.Text)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=True)  # للمصاريف المرتبطة بطلب معين
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'expense_id': self.expense_id,
            'expense_type': self.expense_type,
            'amount': self.amount,
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'description': self.description,
            'order_id': self.order_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Expense {self.expense_type}: {self.amount}>'

