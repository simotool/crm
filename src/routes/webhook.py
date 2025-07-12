from flask import Blueprint, request, jsonify
from src.models import db, Order, Product
from src.services.order_processor import OrderProcessor
from datetime import datetime
import json

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/orders', methods=['POST'])
def receive_order_webhook():
    """استقبال الطلبات عبر Webhook"""
    try:
        # التحقق من Content-Type
        if request.content_type != 'application/json':
            return jsonify({
                'success': False,
                'message': 'Content-Type يجب أن يكون application/json'
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'لا توجد بيانات في الطلب'
            }), 400
        
        # معالجة الطلب
        processor = OrderProcessor()
        result = processor.process_webhook_order(data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'تم استلام الطلب بنجاح',
                'order_id': result['order_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في معالجة الطلب: {str(e)}'
        }), 500

@webhook_bp.route('/webhook/orders/batch', methods=['POST'])
def receive_batch_orders_webhook():
    """استقبال عدة طلبات دفعة واحدة عبر Webhook"""
    try:
        data = request.get_json()
        
        if not data or 'orders' not in data:
            return jsonify({
                'success': False,
                'message': 'يجب أن تحتوي البيانات على مصفوفة orders'
            }), 400
        
        orders_data = data['orders']
        
        if not isinstance(orders_data, list):
            return jsonify({
                'success': False,
                'message': 'orders يجب أن تكون مصفوفة'
            }), 400
        
        processor = OrderProcessor()
        results = []
        successful_orders = 0
        failed_orders = 0
        
        for order_data in orders_data:
            result = processor.process_webhook_order(order_data)
            results.append(result)
            
            if result['success']:
                successful_orders += 1
            else:
                failed_orders += 1
        
        return jsonify({
            'success': True,
            'message': f'تم معالجة {successful_orders} طلب بنجاح، فشل في {failed_orders} طلب',
            'total_orders': len(orders_data),
            'successful_orders': successful_orders,
            'failed_orders': failed_orders,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في معالجة الطلبات: {str(e)}'
        }), 500

@webhook_bp.route('/webhook/test', methods=['POST', 'GET'])
def test_webhook():
    """endpoint لاختبار الـ Webhook"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'message': 'Webhook يعمل بشكل صحيح',
            'timestamp': str(datetime.utcnow())
        }), 200
    
    try:
        data = request.get_json() if request.content_type == 'application/json' else request.form.to_dict()
        
        return jsonify({
            'success': True,
            'message': 'تم استلام البيانات بنجاح',
            'received_data': data,
            'headers': dict(request.headers),
            'method': request.method
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في اختبار الـ Webhook: {str(e)}'
        }), 500

