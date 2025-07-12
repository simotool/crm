from . import db
from datetime import datetime

class Staff(db.Model):
    __tablename__ = 'staff'
    
    staff_id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(100), nullable=False)  # مثال: مؤكد طلبات
    contact_phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='confirmation_staff', lazy=True)
    
    def to_dict(self):
        return {
            'staff_id': self.staff_id,
            'staff_name': self.staff_name,
            'role': self.role,
            'contact_phone': self.contact_phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Staff {self.staff_name} ({self.role})>'

