from flask import Blueprint, request, jsonify
from src.models import db, DeliveryPriceList, Product, DeliveryCompany

delivery_price_list_bp = Blueprint('delivery_price_list', __name__)

@delivery_price_list_bp.route('/delivery-price-lists', methods=['GET'])
def get_delivery_price_lists():
    """جلب جميع قوائم أسعار التوصيل"""
    try:
        # إمكانية التصفية حسب المنتج أو شركة التوصيل
        product_id = request.args.get('product_id')
        company_id = request.args.get('company_id')
        
        query = DeliveryPriceList.query
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        if company_id:
            query = query.filter_by(delivery_company_id=company_id)
        
        price_lists = query.all()
        
        return jsonify({
            'success': True,
            'data': [price_list.to_dict() for price_list in price_lists]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب قوائم أسعار التوصيل: {str(e)}'
        }), 500

@delivery_price_list_bp.route('/delivery-price-lists/<int:price_list_id>', methods=['GET'])
def get_delivery_price_list(price_list_id):
    """جلب قائمة أسعار توصيل محددة"""
    try:
        price_list = DeliveryPriceList.query.get(price_list_id)
        if not price_list:
            return jsonify({
                'success': False,
                'message': 'قائمة أسعار التوصيل غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'data': price_list.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب قائمة أسعار التوصيل: {str(e)}'
        }), 500

@delivery_price_list_bp.route('/delivery-price-lists', methods=['POST'])
def create_delivery_price_list():
    """إنشاء قائمة أسعار توصيل جديدة"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['price_list_name', 'product_id', 'delivery_company_id', 'price_per_unit']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # التحقق من وجود المنتج
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        # التحقق من وجود شركة التوصيل
        company = DeliveryCompany.query.get(data['delivery_company_id'])
        if not company:
            return jsonify({
                'success': False,
                'message': 'شركة التوصيل غير موجودة'
            }), 404
        
        # إنشاء قائمة أسعار التوصيل الجديدة
        price_list = DeliveryPriceList(
            price_list_name=data['price_list_name'],
            product_id=data['product_id'],
            delivery_company_id=data['delivery_company_id'],
            price_per_unit=float(data['price_per_unit']),
            region=data.get('region', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(price_list)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء قائمة أسعار التوصيل بنجاح',
            'data': price_list.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء قائمة أسعار التوصيل: {str(e)}'
        }), 500

@delivery_price_list_bp.route('/delivery-price-lists/<int:price_list_id>', methods=['PUT'])
def update_delivery_price_list(price_list_id):
    """تحديث قائمة أسعار توصيل"""
    try:
        price_list = DeliveryPriceList.query.get(price_list_id)
        if not price_list:
            return jsonify({
                'success': False,
                'message': 'قائمة أسعار التوصيل غير موجودة'
            }), 404
        
        data = request.get_json()
        
        # تحديث البيانات
        if 'price_list_name' in data:
            price_list.price_list_name = data['price_list_name']
        if 'price_per_unit' in data:
            price_list.price_per_unit = float(data['price_per_unit'])
        if 'region' in data:
            price_list.region = data['region']
        if 'is_active' in data:
            price_list.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث قائمة أسعار التوصيل بنجاح',
            'data': price_list.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث قائمة أسعار التوصيل: {str(e)}'
        }), 500

@delivery_price_list_bp.route('/delivery-price-lists/<int:price_list_id>', methods=['DELETE'])
def delete_delivery_price_list(price_list_id):
    """حذف قائمة أسعار توصيل"""
    try:
        price_list = DeliveryPriceList.query.get(price_list_id)
        if not price_list:
            return jsonify({
                'success': False,
                'message': 'قائمة أسعار التوصيل غير موجودة'
            }), 404
        
        db.session.delete(price_list)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف قائمة أسعار التوصيل بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف قائمة أسعار التوصيل: {str(e)}'
        }), 500

@delivery_price_list_bp.route('/delivery-price-lists/calculate', methods=['POST'])
def calculate_delivery_price():
    """حساب سعر التوصيل لطلب معين"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'delivery_company_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        product_id = data['product_id']
        company_id = data['delivery_company_id']
        quantity = int(data['quantity'])
        region = data.get('region', '')
        
        # البحث عن قائمة الأسعار المناسبة
        query = DeliveryPriceList.query.filter_by(
            product_id=product_id,
            delivery_company_id=company_id,
            is_active=True
        )
        
        if region:
            # البحث عن سعر خاص بالمنطقة أولاً
            price_list = query.filter_by(region=region).first()
            if not price_list:
                # إذا لم توجد، البحث عن سعر عام
                price_list = query.filter_by(region='').first()
        else:
            price_list = query.first()
        
        if not price_list:
            return jsonify({
                'success': False,
                'message': 'لا توجد قائمة أسعار متاحة لهذا المنتج وشركة التوصيل'
            }), 404
        
        # حساب السعر الإجمالي
        total_price = price_list.price_per_unit * quantity
        
        return jsonify({
            'success': True,
            'data': {
                'price_list_id': price_list.price_list_id,
                'price_list_name': price_list.price_list_name,
                'price_per_unit': price_list.price_per_unit,
                'quantity': quantity,
                'total_price': total_price,
                'region': price_list.region
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في حساب سعر التوصيل: {str(e)}'
        }), 500

