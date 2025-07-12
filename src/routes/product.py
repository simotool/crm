from flask import Blueprint, request, jsonify
from src.models import db, Product

product_bp = Blueprint('product', __name__)

@product_bp.route('/products', methods=['GET'])
def get_products():
    """جلب جميع المنتجات"""
    try:
        products = Product.query.all()
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المنتجات: {str(e)}'
        }), 500

@product_bp.route('/products/<string:sku>', methods=['GET'])
def get_product_by_sku(sku):
    """جلب منتج بواسطة SKU"""
    try:
        product = Product.query.filter_by(sku=sku).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المنتج: {str(e)}'
        }), 500

@product_bp.route('/products', methods=['POST'])
def create_product():
    """إنشاء منتج جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['product_name', 'sku', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # التحقق من عدم وجود SKU مكرر
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({
                'success': False,
                'message': 'SKU موجود مسبقاً'
            }), 400
        
        # إنشاء المنتج الجديد
        product = Product(
            product_name=data['product_name'],
            sku=data['sku'],
            description=data.get('description', ''),
            price=float(data['price']),
            current_stock=int(data.get('current_stock', 0)),
            initial_stock=int(data.get('initial_stock', 0))
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء المنتج بنجاح',
            'data': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء المنتج: {str(e)}'
        }), 500

@product_bp.route('/products/<string:sku>', methods=['PUT'])
def update_product(sku):
    """تحديث منتج"""
    try:
        product = Product.query.filter_by(sku=sku).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        data = request.get_json()
        
        # تحديث البيانات
        if 'product_name' in data:
            product.product_name = data['product_name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = float(data['price'])
        if 'current_stock' in data:
            product.current_stock = int(data['current_stock'])
        if 'initial_stock' in data:
            product.initial_stock = int(data['initial_stock'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث المنتج بنجاح',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث المنتج: {str(e)}'
        }), 500

@product_bp.route('/products/<string:sku>/stock', methods=['PUT'])
def update_product_stock(sku):
    """تحديث مخزون المنتج"""
    try:
        product = Product.query.filter_by(sku=sku).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        data = request.get_json()
        
        if 'current_stock' not in data:
            return jsonify({
                'success': False,
                'message': 'current_stock مطلوب'
            }), 400
        
        product.current_stock = int(data['current_stock'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث المخزون بنجاح',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث المخزون: {str(e)}'
        }), 500

@product_bp.route('/products/<string:sku>', methods=['DELETE'])
def delete_product(sku):
    """حذف منتج"""
    try:
        product = Product.query.filter_by(sku=sku).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف المنتج بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف المنتج: {str(e)}'
        }), 500

