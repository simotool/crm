from flask import Blueprint, request, jsonify
from src.services.google_sheets import GoogleSheetsService
from src.services.order_processor import OrderProcessor
from datetime import datetime

google_sheets_bp = Blueprint('google_sheets', __name__)

@google_sheets_bp.route('/google-sheets/sync', methods=['POST'])
def sync_orders_from_sheets():
    """مزامنة الطلبات من Google Sheets"""
    try:
        data = request.get_json() or {}
        range_name = data.get('range', 'Sheet1!A:Z')
        
        # إنشاء خدمة Google Sheets
        sheets_service = GoogleSheetsService()
        
        # قراءة البيانات من الجدول
        raw_orders = sheets_service.read_orders_from_sheet(range_name)
        
        if not raw_orders:
            return jsonify({
                'success': True,
                'message': 'لا توجد طلبات جديدة في الجدول',
                'processed_orders': 0
            }), 200
        
        # معالجة الطلبات
        processor = OrderProcessor()
        results = []
        successful_orders = 0
        failed_orders = 0
        
        for i, raw_order in enumerate(raw_orders):
            # تحويل البيانات
            order_data = sheets_service.parse_order_data(raw_order)
            
            if not order_data:
                results.append({
                    'row': i + 2,  # +2 لأن الصف الأول headers والفهرسة تبدأ من 1
                    'success': False,
                    'message': 'فشل في تحويل بيانات الطلب'
                })
                failed_orders += 1
                continue
            
            # التحقق من صحة البيانات
            is_valid, validation_message = sheets_service.validate_order_data(order_data)
            
            if not is_valid:
                results.append({
                    'row': i + 2,
                    'success': False,
                    'message': validation_message
                })
                failed_orders += 1
                continue
            
            # معالجة الطلب
            result = processor.process_google_sheets_order(order_data)
            result['row'] = i + 2
            results.append(result)
            
            if result['success']:
                successful_orders += 1
                # وضع علامة على الطلب كمعالج في الجدول
                sheets_service.mark_order_as_processed(i + 1)
            else:
                failed_orders += 1
        
        return jsonify({
            'success': True,
            'message': f'تم معالجة {successful_orders} طلب بنجاح، فشل في {failed_orders} طلب',
            'total_orders': len(raw_orders),
            'successful_orders': successful_orders,
            'failed_orders': failed_orders,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في مزامنة الطلبات من Google Sheets: {str(e)}'
        }), 500

@google_sheets_bp.route('/google-sheets/test-connection', methods=['GET'])
def test_google_sheets_connection():
    """اختبار الاتصال مع Google Sheets"""
    try:
        sheets_service = GoogleSheetsService()
        
        # محاولة قراءة صف واحد للاختبار
        test_data = sheets_service.read_orders_from_sheet('Sheet1!A1:A1')
        
        return jsonify({
            'success': True,
            'message': 'تم الاتصال بـ Google Sheets بنجاح',
            'test_data': test_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'فشل في الاتصال بـ Google Sheets: {str(e)}'
        }), 500

@google_sheets_bp.route('/google-sheets/preview', methods=['POST'])
def preview_sheet_data():
    """معاينة البيانات من Google Sheets دون معالجة"""
    try:
        data = request.get_json() or {}
        range_name = data.get('range', 'Sheet1!A:Z')
        max_rows = data.get('max_rows', 10)
        
        sheets_service = GoogleSheetsService()
        
        # قراءة البيانات
        raw_orders = sheets_service.read_orders_from_sheet(range_name)
        
        # أخذ عدد محدود من الصفوف للمعاينة
        preview_data = raw_orders[:max_rows] if raw_orders else []
        
        # تحويل البيانات للمعاينة
        processed_preview = []
        for raw_order in preview_data:
            order_data = sheets_service.parse_order_data(raw_order)
            is_valid, validation_message = sheets_service.validate_order_data(order_data) if order_data else (False, 'فشل في تحويل البيانات')
            
            processed_preview.append({
                'raw_data': raw_order,
                'processed_data': order_data,
                'is_valid': is_valid,
                'validation_message': validation_message
            })
        
        return jsonify({
            'success': True,
            'total_rows': len(raw_orders),
            'preview_rows': len(preview_data),
            'data': processed_preview
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في معاينة البيانات: {str(e)}'
        }), 500

