import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
from typing import List, Dict, Any

class GoogleSheetsService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SHEETS_API_KEY')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """تهيئة خدمة Google Sheets API"""
        try:
            if self.api_key:
                # استخدام API Key
                self.service = build('sheets', 'v4', developerKey=self.api_key)
            else:
                # يمكن إضافة Service Account credentials هنا لاحقاً
                raise ValueError("Google Sheets API Key غير موجود")
        except Exception as e:
            print(f"خطأ في تهيئة Google Sheets Service: {str(e)}")
    
    def read_orders_from_sheet(self, range_name: str = 'Sheet1!A:Z') -> List[Dict[str, Any]]:
        """قراءة الطلبات من Google Sheet"""
        try:
            if not self.service:
                raise ValueError("Google Sheets Service غير مهيأ")
            
            # قراءة البيانات من الجدول
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # افتراض أن الصف الأول يحتوي على أسماء الأعمدة
            headers = values[0]
            orders = []
            
            for row in values[1:]:
                # التأكد من أن الصف يحتوي على بيانات
                if len(row) > 0:
                    order_data = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            order_data[header] = row[i]
                        else:
                            order_data[header] = ''
                    orders.append(order_data)
            
            return orders
            
        except Exception as e:
            print(f"خطأ في قراءة البيانات من Google Sheets: {str(e)}")
            return []
    
    def parse_order_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحويل البيانات الخام إلى تنسيق الطلب المطلوب"""
        try:
            # تحديد mapping للأعمدة (يمكن تخصيصه حسب تنسيق الجدول)
            order_data = {
                'customer_name': raw_data.get('اسم العميل', raw_data.get('Customer Name', '')),
                'customer_phone': raw_data.get('رقم الهاتف', raw_data.get('Phone', '')),
                'customer_address': raw_data.get('العنوان', raw_data.get('Address', '')),
                'product_sku': raw_data.get('رمز المنتج', raw_data.get('Product SKU', '')),
                'quantity': int(raw_data.get('الكمية', raw_data.get('Quantity', 1))),
                'order_source': 'Google Sheet',
                'notes': raw_data.get('ملاحظات', raw_data.get('Notes', ''))
            }
            
            return order_data
            
        except Exception as e:
            print(f"خطأ في تحويل بيانات الطلب: {str(e)}")
            return None
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> tuple[bool, str]:
        """التحقق من صحة بيانات الطلب"""
        required_fields = ['customer_name', 'customer_phone', 'customer_address', 'product_sku']
        
        for field in required_fields:
            if not order_data.get(field):
                return False, f"الحقل {field} مطلوب"
        
        # التحقق من صحة رقم الهاتف (تحقق بسيط)
        phone = order_data.get('customer_phone', '')
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            return False, "رقم الهاتف غير صحيح"
        
        # التحقق من الكمية
        try:
            quantity = int(order_data.get('quantity', 1))
            if quantity <= 0:
                return False, "الكمية يجب أن تكون أكبر من صفر"
        except ValueError:
            return False, "الكمية يجب أن تكون رقم صحيح"
        
        return True, "البيانات صحيحة"
    
    def mark_order_as_processed(self, row_number: int, sheet_name: str = 'Sheet1'):
        """وضع علامة على الطلب كمعالج في الجدول"""
        try:
            if not self.service:
                return False
            
            # إضافة عمود "معالج" أو تحديث حالة الطلب
            range_name = f"{sheet_name}!Z{row_number + 1}"  # العمود Z للحالة
            
            body = {
                'values': [['معالج']]
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"خطأ في تحديث حالة الطلب في الجدول: {str(e)}")
            return False

