from . import db
from datetime import datetime

class DeliveryCompany(db.Model):
    __tablename__ = 'delivery_companies'
    
    company_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    api_endpoint = db.Column(db.String(500))
    api_key = db.Column(db.String(255))
    contact_person = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='delivery_company', lazy=True)
    delivery_price_lists = db.relationship('DeliveryPriceList', backref='delivery_company', lazy=True)
    
    def to_dict(self):
        return {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'api_endpoint': self.api_endpoint,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DeliveryCompany {self.company_name}>'

