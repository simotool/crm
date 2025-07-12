from flask import Blueprint, request, jsonify
from src.models import db, Product, Order
from sqlalchemy import func
from datetime import datetime, timedelta

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory/status', methods=['GET'])
def get_inventory_status():
    """جلب حالة المخزون العامة"""
    try:
        # إحصائيات عامة
        total_products = Product.query.count()
        low_stock_threshold = int(request.args.get('low_stock_threshold', 10))
        
        # المنتجات منخفضة المخزون
        low_stock_products = Product.query.filter(
            Product.current_stock <= low_stock_threshold
        ).all()
        
        # المنتجات نفدت من المخزون
        out_of_stock_products = Product.query.filter(
            Product.current_stock <= 0
        ).all()
        
        # إجمالي قيمة المخزون
        total_inventory_value = db.session.query(
            func.sum(Product.current_stock * Product.price)
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': total_products,
                'low_stock_count': len(low_stock_products),
                'out_of_stock_count': len(out_of_stock_products),
                'total_inventory_value': float(total_inventory_value),
                'low_stock_products': [product.to_dict() for product in low_stock_products],
                'out_of_stock_products': [product.to_dict() for product in out_of_stock_products]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب حالة المخزون: {str(e)}'
        }), 500

@inventory_bp.route('/inventory/alerts', methods=['GET'])
def get_inventory_alerts():
    """جلب تنبيهات المخزون"""
    try:
        low_stock_threshold = int(request.args.get('low_stock_threshold', 10))
        
        alerts = []
        
        # تنبيهات المخزون المنخفض
        low_stock_products = Product.query.filter(
            Product.current_stock <= low_stock_threshold,
            Product.current_stock > 0
        ).all()
        
        for product in low_stock_products:
            alerts.append({
                'type': 'low_stock',
                'severity': 'warning',
                'product_id': product.product_id,
                'product_name': product.product_name,
                'sku': product.sku,
                'current_stock': product.current_stock,
                'message': f'المخزون منخفض للمنتج {product.product_name} (متبقي: {product.current_stock})'
            })
        
        # تنبيهات نفاد المخزون
        out_of_stock_products = Product.query.filter(
            Product.current_stock <= 0
        ).all()
        
        for product in out_of_stock_products:
            alerts.append({
                'type': 'out_of_stock',
                'severity': 'critical',
                'product_id': product.product_id,
                'product_name': product.product_name,
                'sku': product.sku,
                'current_stock': product.current_stock,
                'message': f'نفد المخزون للمنتج {product.product_name}'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'total_alerts': len(alerts)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب تنبيهات المخزون: {str(e)}'
        }), 500

@inventory_bp.route('/inventory/movement', methods=['GET'])
def get_inventory_movement():
    """جلب تقرير حركة المخزون"""
    try:
        # فترة التقرير
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # الطلبات في الفترة المحددة
        orders = Order.query.filter(
            Order.order_date >= start_date,
            Order.order_status.in_(['مؤكد', 'تم الشحن', 'تم التسليم'])
        ).all()
        
        # تجميع البيانات حسب المنتج
        movement_data = {}
        
        for order in orders:
            product_id = order.product_id
            if product_id not in movement_data:
                product = Product.query.get(product_id)
                movement_data[product_id] = {
                    'product_id': product_id,
                    'product_name': product.product_name if product else 'منتج محذوف',
                    'sku': product.sku if product else '',
                    'total_sold': 0,
                    'orders_count': 0,
                    'current_stock': product.current_stock if product else 0
                }
            
            movement_data[product_id]['total_sold'] += order.quantity
            movement_data[product_id]['orders_count'] += 1
        
        # ترتيب حسب الأكثر مبيعاً
        sorted_movement = sorted(
            movement_data.values(),
            key=lambda x: x['total_sold'],
            reverse=True
        )
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'movement': sorted_movement,
                'total_products': len(sorted_movement)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب تقرير حركة المخزون: {str(e)}'
        }), 500

@inventory_bp.route('/inventory/restock', methods=['POST'])
def restock_product():
    """إعادة تعبئة مخزون منتج"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        product_id = data['product_id']
        quantity = int(data['quantity'])
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'الكمية يجب أن تكون أكبر من صفر'
            }), 400
        
        # البحث عن المنتج
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        # تحديث المخزون
        old_stock = product.current_stock
        product.current_stock += quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تعبئة المخزون بنجاح. المخزون السابق: {old_stock}، المخزون الحالي: {product.current_stock}',
            'data': {
                'product_id': product_id,
                'old_stock': old_stock,
                'added_quantity': quantity,
                'new_stock': product.current_stock
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تعبئة المخزون: {str(e)}'
        }), 500

@inventory_bp.route('/inventory/adjust', methods=['POST'])
def adjust_inventory():
    """تعديل المخزون (زيادة أو نقصان)"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'adjustment', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        product_id = data['product_id']
        adjustment = int(data['adjustment'])  # يمكن أن يكون موجب أو سالب
        reason = data['reason']
        
        # البحث عن المنتج
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
        
        # التحقق من أن التعديل لن يجعل المخزون سالباً
        new_stock = product.current_stock + adjustment
        if new_stock < 0:
            return jsonify({
                'success': False,
                'message': f'لا يمكن تقليل المخزون إلى {new_stock}. المخزون الحالي: {product.current_stock}'
            }), 400
        
        # تحديث المخزون
        old_stock = product.current_stock
        product.current_stock = new_stock
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تعديل المخزون بنجاح. السبب: {reason}',
            'data': {
                'product_id': product_id,
                'old_stock': old_stock,
                'adjustment': adjustment,
                'new_stock': product.current_stock,
                'reason': reason
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تعديل المخزون: {str(e)}'
        }), 500

