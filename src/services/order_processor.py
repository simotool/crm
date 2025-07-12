from src.models import db, Order, Product
from typing import Dict, Any
import re

class OrderProcessor:
    def __init__(self):
        pass
    
    def process_webhook_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة طلب واحد من Webhook"""
        try:
            # تحويل البيانات إلى تنسيق موحد
            order_data = self.parse_webhook_data(data)
            
            if not order_data:
                return {
                    'success': False,
                    'message': 'فشل في تحويل بيانات الطلب'
                }
            
            # التحقق من صحة البيانات
            is_valid, validation_message = self.validate_order_data(order_data)
            
            if not is_valid:
                return {
                    'success': False,
                    'message': validation_message
                }
            
            # البحث عن المنتج
            product = Product.query.filter_by(sku=order_data['product_sku']).first()
            
            if not product:
                return {
                    'success': False,
                    'message': f'المنتج برمز {order_data["product_sku"]} غير موجود'
                }
            
            # التحقق من توفر المخزون
            if product.current_stock < order_data['quantity']:
                return {
                    'success': False,
                    'message': f'المخزون غير كافي. المتوفر: {product.current_stock}, المطلوب: {order_data["quantity"]}'
                }
            
            # إنشاء الطلب
            order = Order(
                customer_name=order_data['customer_name'],
                customer_phone=order_data['customer_phone'],
                customer_address=order_data['customer_address'],
                product_id=product.product_id,
                quantity=order_data['quantity'],
                order_source=order_data['order_source'],
                notes=order_data.get('notes', '')
            )
            
            # تقليل المخزون
            product.current_stock -= order_data['quantity']
            
            db.session.add(order)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'تم إنشاء الطلب بنجاح',
                'order_id': order.order_id
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'خطأ في معالجة الطلب: {str(e)}'
            }
    
    def process_google_sheets_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة طلب من Google Sheets"""
        try:
            # تحويل البيانات إلى تنسيق موحد
            order_data = self.parse_google_sheets_data(data)
            
            if not order_data:
                return {
                    'success': False,
                    'message': 'فشل في تحويل بيانات الطلب من Google Sheets'
                }
            
            # استخدام نفس منطق معالجة الطلبات
            return self.process_webhook_order(order_data)
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في معالجة طلب Google Sheets: {str(e)}'
            }
    
    def parse_webhook_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """تحويل بيانات Webhook إلى تنسيق موحد"""
        try:
            order_data = {
                'customer_name': data.get('customer_name', data.get('name', '')),
                'customer_phone': data.get('customer_phone', data.get('phone', '')),
                'customer_address': data.get('customer_address', data.get('address', '')),
                'product_sku': data.get('product_sku', data.get('sku', '')),
                'quantity': int(data.get('quantity', 1)),
                'order_source': 'Webhook',
                'notes': data.get('notes', data.get('comments', ''))
            }
            
            return order_data
            
        except Exception as e:
            print(f"خطأ في تحويل بيانات Webhook: {str(e)}")
            return None
    
    def parse_google_sheets_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """تحويل بيانات Google Sheets إلى تنسيق موحد"""
        try:
            order_data = {
                'customer_name': data.get('اسم العميل', data.get('Customer Name', '')),
                'customer_phone': data.get('رقم الهاتف', data.get('Phone', '')),
                'customer_address': data.get('العنوان', data.get('Address', '')),
                'product_sku': data.get('رمز المنتج', data.get('Product SKU', '')),
                'quantity': int(data.get('الكمية', data.get('Quantity', 1))),
                'order_source': 'Google Sheet',
                'notes': data.get('ملاحظات', data.get('Notes', ''))
            }
            
            return order_data
            
        except Exception as e:
            print(f"خطأ في تحويل بيانات Google Sheets: {str(e)}")
            return None
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> tuple[bool, str]:
        """التحقق من صحة بيانات الطلب"""
        required_fields = ['customer_name', 'customer_phone', 'customer_address', 'product_sku']
        
        for field in required_fields:
            if not order_data.get(field):
                return False, f"الحقل {field} مطلوب"
        
        # التحقق من صحة رقم الهاتف
        phone = order_data.get('customer_phone', '')
        if not self.validate_phone_number(phone):
            return False, "رقم الهاتف غير صحيح"
        
        # التحقق من الكمية
        try:
            quantity = int(order_data.get('quantity', 1))
            if quantity <= 0:
                return False, "الكمية يجب أن تكون أكبر من صفر"
        except ValueError:
            return False, "الكمية يجب أن تكون رقم صحيح"
        
        return True, "البيانات صحيحة"
    
    def validate_phone_number(self, phone: str) -> bool:
        """التحقق من صحة رقم الهاتف"""
        if not phone:
            return False
        
        # إزالة المسافات والرموز الشائعة
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # التحقق من أن الرقم يحتوي على أرقام فقط (مع إمكانية وجود + في البداية)
        if clean_phone.startswith('+'):
            clean_phone = clean_phone[1:]
        
        if not clean_phone.isdigit():
            return False
        
        # التحقق من طول الرقم (بين 8 و 15 رقم)
        if len(clean_phone) < 8 or len(clean_phone) > 15:
            return False
        
        return True
    
    def normalize_phone_number(self, phone: str) -> str:
        """توحيد تنسيق رقم الهاتف"""
        if not phone:
            return phone
        
        # إزالة المسافات والرموز
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # إضافة رمز الدولة الجزائري إذا لم يكن موجوداً
        if not clean_phone.startswith('+'):
            if clean_phone.startswith('0'):
                clean_phone = '+213' + clean_phone[1:]
            elif not clean_phone.startswith('213'):
                clean_phone = '+213' + clean_phone
            else:
                clean_phone = '+' + clean_phone
        
        return clean_phone

