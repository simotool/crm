from flask import Blueprint, request, jsonify
from src.models import db, Order, DeliveryCompany
from src.services.delivery_integration import DeliveryManager, DeliveryServiceFactory
from datetime import datetime

delivery_integration_bp = Blueprint('delivery_integration', __name__)

# إنشاء مدير التوصيل العام
delivery_manager = DeliveryManager()

# تسجيل الخدمات المتاحة
try:
    yalidine_service = DeliveryServiceFactory.create_service('yalidine')
    delivery_manager.register_service('yalidine', yalidine_service)
except Exception as e:
    print(f"فشل في تسجيل خدمة Yalidine: {str(e)}")

try:
    aramex_service = DeliveryServiceFactory.create_service('aramex')
    delivery_manager.register_service('aramex', aramex_service)
except Exception as e:
    print(f"فشل في تسجيل خدمة Aramex: {str(e)}")

@delivery_integration_bp.route('/delivery/services', methods=['GET'])
def get_available_services():
    """جلب قائمة بخدمات التوصيل المتاحة"""
    try:
        services = delivery_manager.get_available_services()
        
        # جلب معلومات إضافية من قاعدة البيانات
        db_companies = DeliveryCompany.query.filter_by(is_active=True).all()
        
        service_details = []
        for service_name in services:
            # البحث عن الشركة في قاعدة البيانات
            db_company = next((c for c in db_companies if c.company_name.lower() == service_name), None)
            
            service_details.append({
                'service_name': service_name,
                'display_name': service_name.title(),
                'is_configured': True,  # لأنها مسجلة في المدير
                'database_info': db_company.to_dict() if db_company else None
            })
        
        return jsonify({
            'success': True,
            'services': service_details,
            'total_services': len(services)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب خدمات التوصيل: {str(e)}'
        }), 500

@delivery_integration_bp.route('/delivery/create-shipment', methods=['POST'])
def create_shipment():
    """إنشاء شحنة جديدة"""
    try:
        data = request.get_json()
        
        required_fields = ['service_name', 'order_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        service_name = data['service_name']
        order_id = data['order_id']
        
        # جلب الطلب من قاعدة البيانات
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'الطلب غير موجود'
            }), 404
        
        # تحضير بيانات الشحنة
        shipment_data = {
            'order_id': str(order.order_id),
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'customer_address': order.customer_address,
            'product_description': f'طلب رقم {order.order_id}',
            'total_amount': float(order.total_amount or 0),
            'weight': data.get('weight', 1),
            'length': data.get('length', 10),
            'width': data.get('width', 10),
            'height': data.get('height', 10),
            'declared_value': float(order.total_amount or 0),
            'insurance': data.get('insurance', False),
            'free_shipping': data.get('free_shipping', False),
            'from_wilaya': data.get('from_wilaya', 'الجزائر'),
            'to_wilaya': data.get('to_wilaya', ''),
            'to_commune': data.get('to_commune', ''),
            'sender_name': data.get('sender_name', ''),
            'sender_company': data.get('sender_company', ''),
            'sender_phone': data.get('sender_phone', ''),
            'sender_address': data.get('sender_address', ''),
            'sender_email': data.get('sender_email', ''),
            'customer_email': data.get('customer_email', ''),
            'comments': data.get('comments', order.notes or '')
        }
        
        # إنشاء الشحنة
        result = delivery_manager.create_shipment_with_service(service_name, shipment_data)
        
        if result['success']:
            # تحديث الطلب بمعلومات الشحنة
            order.tracking_number = result.get('tracking_number', '')
            order.delivery_company_id = data.get('delivery_company_id')
            order.order_status = 'تم الشحن'
            order.shipped_date = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'تم إنشاء الشحنة وتحديث الطلب بنجاح',
                'order_id': order_id,
                'tracking_number': result.get('tracking_number', ''),
                'shipment_data': result
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'فشل في إنشاء الشحنة'),
                'details': result
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الشحنة: {str(e)}'
        }), 500

@delivery_integration_bp.route('/delivery/track/<tracking_number>', methods=['GET'])
def track_shipment(tracking_number):
    """تتبع شحنة"""
    try:
        service_name = request.args.get('service_name')
        
        if not service_name:
            # محاولة العثور على الخدمة من قاعدة البيانات
            order = Order.query.filter_by(tracking_number=tracking_number).first()
            if order and order.delivery_company:
                service_name = order.delivery_company.company_name.lower()
            else:
                return jsonify({
                    'success': False,
                    'message': 'يجب تحديد اسم خدمة التوصيل أو وجود الطلب في قاعدة البيانات'
                }), 400
        
        # تتبع الشحنة
        result = delivery_manager.track_shipment_with_service(service_name, tracking_number)
        
        if result['success']:
            # تحديث حالة الطلب إذا كان موجوداً
            order = Order.query.filter_by(tracking_number=tracking_number).first()
            if order:
                # تحديث حالة الطلب بناءً على حالة الشحنة
                status_mapping = {
                    'delivered': 'تم التسليم',
                    'in_transit': 'في الطريق',
                    'out_for_delivery': 'خرج للتسليم',
                    'returned': 'مرتجع',
                    'cancelled': 'ملغي'
                }
                
                shipment_status = result.get('status', '').lower()
                new_order_status = status_mapping.get(shipment_status, order.order_status)
                
                if new_order_status != order.order_status:
                    order.order_status = new_order_status
                    order.last_status_update = datetime.utcnow()
                    db.session.commit()
            
            return jsonify({
                'success': True,
                'tracking_number': tracking_number,
                'service_name': service_name,
                'tracking_data': result,
                'order_updated': order is not None
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'فشل في تتبع الشحنة'),
                'details': result
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تتبع الشحنة: {str(e)}'
        }), 500

@delivery_integration_bp.route('/delivery/calculate-cost', methods=['POST'])
def calculate_shipping_cost():
    """حساب تكلفة الشحن"""
    try:
        data = request.get_json()
        
        required_fields = ['service_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        service_name = data['service_name']
        
        # تحضير بيانات حساب التكلفة
        cost_data = {
            'from_wilaya': data.get('from_wilaya', 'الجزائر'),
            'to_wilaya': data.get('to_wilaya', ''),
            'weight': data.get('weight', 1),
            'length': data.get('length', 10),
            'width': data.get('width', 10),
            'height': data.get('height', 10),
            'declared_value': float(data.get('declared_value', 0)),
            'sender_address': data.get('sender_address', ''),
            'sender_city': data.get('sender_city', 'Algiers'),
            'customer_address': data.get('customer_address', ''),
            'customer_city': data.get('customer_city', ''),
            'product_description': data.get('product_description', '')
        }
        
        # حساب التكلفة
        service = delivery_manager.get_service(service_name)
        if not service:
            return jsonify({
                'success': False,
                'message': f'خدمة التوصيل {service_name} غير متاحة'
            }), 404
        
        result = service.get_shipping_cost(cost_data)
        
        return jsonify({
            'success': result['success'],
            'service_name': service_name,
            'cost_data': result,
            'input_data': cost_data
        }), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في حساب تكلفة الشحن: {str(e)}'
        }), 500

@delivery_integration_bp.route('/delivery/bulk-track', methods=['POST'])
def bulk_track_shipments():
    """تتبع عدة شحنات دفعة واحدة"""
    try:
        data = request.get_json()
        
        if 'tracking_numbers' not in data:
            return jsonify({
                'success': False,
                'message': 'قائمة أرقام التتبع مطلوبة'
            }), 400
        
        tracking_numbers = data['tracking_numbers']
        service_name = data.get('service_name')
        
        results = []
        
        for tracking_number in tracking_numbers:
            try:
                # تحديد خدمة التوصيل إذا لم تكن محددة
                current_service = service_name
                if not current_service:
                    order = Order.query.filter_by(tracking_number=tracking_number).first()
                    if order and order.delivery_company:
                        current_service = order.delivery_company.company_name.lower()
                
                if current_service:
                    result = delivery_manager.track_shipment_with_service(current_service, tracking_number)
                    results.append({
                        'tracking_number': tracking_number,
                        'service_name': current_service,
                        'result': result
                    })
                else:
                    results.append({
                        'tracking_number': tracking_number,
                        'service_name': None,
                        'result': {
                            'success': False,
                            'message': 'لا يمكن تحديد خدمة التوصيل'
                        }
                    })
                    
            except Exception as e:
                results.append({
                    'tracking_number': tracking_number,
                    'service_name': current_service,
                    'result': {
                        'success': False,
                        'message': f'خطأ في التتبع: {str(e)}'
                    }
                })
        
        # إحصائيات
        successful_tracks = sum(1 for r in results if r['result']['success'])
        failed_tracks = len(results) - successful_tracks
        
        return jsonify({
            'success': True,
            'total_shipments': len(tracking_numbers),
            'successful_tracks': successful_tracks,
            'failed_tracks': failed_tracks,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في التتبع المجمع: {str(e)}'
        }), 500

