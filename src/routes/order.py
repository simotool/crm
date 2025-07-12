from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models import db, Order, Product, Staff, DeliveryCompany

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
def get_orders():
    """جلب جميع الطلبات"""
    try:
        # إمكانية التصفية حسب الحالة
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        query = Order.query
        
        if status:
            query = query.filter_by(order_status=status)
        
        orders = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [order.to_dict() for order in orders.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': orders.total,
                'pages': orders.pages
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الطلبات: {str(e)}'
        }), 500

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """جلب طلب محدد"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'الطلب غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': order.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الطلب: {str(e)}'
        }), 500

@order_bp.route('/orders', methods=['POST'])
def create_order():
    """إنشاء طلب جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['customer_name', 'customer_phone', 'customer_address', 'product_id', 'order_source']
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
        
        # التحقق من توفر المخزون
        quantity = int(data.get('quantity', 1))
        if product.current_stock < quantity:
            return jsonify({
                'success': False,
                'message': 'المخزون غير كافي'
            }), 400
        
        # إنشاء الطلب الجديد
        order = Order(
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_address=data['customer_address'],
            product_id=data['product_id'],
            quantity=quantity,
            order_source=data['order_source'],
            notes=data.get('notes', '')
        )
        
        # تقليل المخزون
        product.current_stock -= quantity
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء الطلب بنجاح',
            'data': order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الطلب: {str(e)}'
        }), 500

@order_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """تحديث حالة الطلب"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'الطلب غير موجود'
            }), 404
        
        data = request.get_json()
        
        if 'order_status' not in data:
            return jsonify({
                'success': False,
                'message': 'order_status مطلوب'
            }), 400
        
        new_status = data['order_status']
        old_status = order.order_status
        
        # تحديث الحالة والتواريخ المناسبة
        order.order_status = new_status
        
        current_time = datetime.utcnow()
        
        if new_status == 'اتصال أول' and not order.first_call_date:
            order.first_call_date = current_time
        elif new_status == 'اتصال ثانٍ' and not order.second_call_date:
            order.second_call_date = current_time
        elif new_status == 'مؤكد' and not order.confirmed_date:
            order.confirmed_date = current_time
        elif new_status == 'تم الشحن' and not order.shipped_date:
            order.shipped_date = current_time
        elif new_status == 'تم التسليم' and not order.delivered_date:
            order.delivered_date = current_time
        elif new_status == 'ملغى' and not order.cancelled_date:
            order.cancelled_date = current_time
            # إرجاع المخزون في حالة الإلغاء
            if old_status not in ['ملغى', 'مرتجع']:
                product = Product.query.get(order.product_id)
                if product:
                    product.current_stock += order.quantity
        elif new_status == 'مرتجع' and not order.returned_date:
            order.returned_date = current_time
            # إرجاع المخزون في حالة الإرجاع
            if old_status not in ['ملغى', 'مرتجع']:
                product = Product.query.get(order.product_id)
                if product:
                    product.current_stock += order.quantity
        
        # تحديث موظف التأكيد إذا تم تمريره
        if 'confirmation_staff_id' in data:
            order.confirmation_staff_id = data['confirmation_staff_id']
        
        # تحديث شركة التوصيل إذا تم تمريرها
        if 'delivery_company_id' in data:
            order.delivery_company_id = data['delivery_company_id']
        
        # تحديث سعر التوصيل إذا تم تمريره
        if 'delivery_price' in data:
            order.delivery_price = float(data['delivery_price'])
        
        # تحديث رقم التتبع إذا تم تمريره
        if 'shipping_tracking_id' in data:
            order.shipping_tracking_id = data['shipping_tracking_id']
        
        # تحديث الملاحظات إذا تم تمريرها
        if 'notes' in data:
            order.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث حالة الطلب بنجاح',
            'data': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث حالة الطلب: {str(e)}'
        }), 500

@order_bp.route('/orders/<int:order_id>/tracking', methods=['GET'])
def get_order_tracking(order_id):
    """جلب معلومات تتبع الطلب"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'الطلب غير موجود'
            }), 404
        
        tracking_info = {
            'order_id': order.order_id,
            'order_status': order.order_status,
            'shipping_tracking_id': order.shipping_tracking_id,
            'delivery_company': order.delivery_company.company_name if order.delivery_company else None,
            'timeline': []
        }
        
        # إنشاء خط زمني للطلب
        if order.order_date:
            tracking_info['timeline'].append({
                'status': 'تم إنشاء الطلب',
                'date': order.order_date.isoformat(),
                'description': 'تم استلام الطلب'
            })
        
        if order.first_call_date:
            tracking_info['timeline'].append({
                'status': 'اتصال أول',
                'date': order.first_call_date.isoformat(),
                'description': 'تم الاتصال الأول بالعميل'
            })
        
        if order.second_call_date:
            tracking_info['timeline'].append({
                'status': 'اتصال ثانٍ',
                'date': order.second_call_date.isoformat(),
                'description': 'تم الاتصال الثاني بالعميل'
            })
        
        if order.confirmed_date:
            tracking_info['timeline'].append({
                'status': 'مؤكد',
                'date': order.confirmed_date.isoformat(),
                'description': 'تم تأكيد الطلب'
            })
        
        if order.shipped_date:
            tracking_info['timeline'].append({
                'status': 'تم الشحن',
                'date': order.shipped_date.isoformat(),
                'description': 'تم شحن الطلب'
            })
        
        if order.delivered_date:
            tracking_info['timeline'].append({
                'status': 'تم التسليم',
                'date': order.delivered_date.isoformat(),
                'description': 'تم تسليم الطلب للعميل'
            })
        
        if order.cancelled_date:
            tracking_info['timeline'].append({
                'status': 'ملغى',
                'date': order.cancelled_date.isoformat(),
                'description': 'تم إلغاء الطلب'
            })
        
        if order.returned_date:
            tracking_info['timeline'].append({
                'status': 'مرتجع',
                'date': order.returned_date.isoformat(),
                'description': 'تم إرجاع الطلب'
            })
        
        return jsonify({
            'success': True,
            'data': tracking_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب معلومات التتبع: {str(e)}'
        }), 500

