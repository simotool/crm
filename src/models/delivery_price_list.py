from . import db
from datetime import datetime

class DeliveryPriceList(db.Model):
    __tablename__ = 'delivery_price_lists'
    
    price_list_id = db.Column(db.Integer, primary_key=True)
    price_list_name = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    delivery_company_id = db.Column(db.Integer, db.ForeignKey('delivery_companies.company_id'), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    region = db.Column(db.String(255))  # المنطقة التي ينطبق عليها السعر
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'price_list_id': self.price_list_id,
            'price_list_name': self.price_list_name,
            'product_id': self.product_id,
            'delivery_company_id': self.delivery_company_id,
            'price_per_unit': self.price_per_unit,
            'region': self.region,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DeliveryPriceList {self.price_list_name}>'

