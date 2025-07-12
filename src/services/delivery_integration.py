import requests
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import os

class DeliveryServiceInterface(ABC):
    """واجهة عامة لجميع خدمات التوصيل"""
    
    @abstractmethod
    def create_shipment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء شحنة جديدة"""
        pass
    
    @abstractmethod
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """تتبع الشحنة"""
        pass
    
    @abstractmethod
    def cancel_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """إلغاء الشحنة"""
        pass
    
    @abstractmethod
    def get_shipping_cost(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب تكلفة الشحن"""
        pass

class YalidineService(DeliveryServiceInterface):
    """خدمة التكامل مع Yalidine Express"""
    
    def __init__(self):
        self.api_key = os.getenv('YALIDINE_API_KEY', '')
        self.base_url = 'https://api.yalidine.app/v1'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def create_shipment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء شحنة جديدة في Yalidine"""
        try:
            # تحويل بيانات الطلب إلى تنسيق Yalidine
            yalidine_data = {
                'from_wilaya_name': order_data.get('from_wilaya', 'الجزائر'),
                'to_wilaya_name': order_data.get('to_wilaya', ''),
                'to_commune_name': order_data.get('to_commune', ''),
                'recipient_name': order_data.get('customer_name', ''),
                'recipient_phone': order_data.get('customer_phone', ''),
                'recipient_address': order_data.get('customer_address', ''),
                'product_list': order_data.get('product_list', ''),
                'price': float(order_data.get('total_amount', 0)),
                'do_insurance': order_data.get('insurance', False),
                'declared_value': float(order_data.get('declared_value', 0)),
                'height': order_data.get('height', 10),
                'width': order_data.get('width', 10),
                'length': order_data.get('length', 10),
                'weight': order_data.get('weight', 1),
                'freeshipping': order_data.get('free_shipping', False),
                'is_stopdesk': order_data.get('stop_desk', False)
            }
            
            response = requests.post(
                f'{self.base_url}/parcels/',
                headers=self.headers,
                json=yalidine_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'tracking_number': result.get('tracking', ''),
                    'shipment_id': result.get('id', ''),
                    'message': 'تم إنشاء الشحنة بنجاح',
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'message': f'فشل في إنشاء الشحنة: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إنشاء الشحنة: {str(e)}'
            }
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """تتبع الشحنة في Yalidine"""
        try:
            response = requests.get(
                f'{self.base_url}/parcels/{tracking_number}/tracking',
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'tracking_number': tracking_number,
                    'status': result.get('status', ''),
                    'last_update': result.get('last_update', ''),
                    'tracking_history': result.get('tracking_history', []),
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'message': f'فشل في تتبع الشحنة: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تتبع الشحنة: {str(e)}'
            }
    
    def cancel_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """إلغاء الشحنة في Yalidine"""
        try:
            response = requests.delete(
                f'{self.base_url}/parcels/{tracking_number}',
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'تم إلغاء الشحنة بنجاح',
                    'tracking_number': tracking_number
                }
            else:
                return {
                    'success': False,
                    'message': f'فشل في إلغاء الشحنة: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إلغاء الشحنة: {str(e)}'
            }
    
    def get_shipping_cost(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب تكلفة الشحن في Yalidine"""
        try:
            cost_data = {
                'from_wilaya_name': order_data.get('from_wilaya', 'الجزائر'),
                'to_wilaya_name': order_data.get('to_wilaya', ''),
                'weight': order_data.get('weight', 1),
                'declared_value': float(order_data.get('declared_value', 0))
            }
            
            response = requests.post(
                f'{self.base_url}/deliveryfees/',
                headers=self.headers,
                json=cost_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'delivery_cost': result.get('delivery_cost', 0),
                    'return_cost': result.get('return_cost', 0),
                    'total_cost': result.get('total_cost', 0),
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'message': f'فشل في حساب تكلفة الشحن: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في حساب تكلفة الشحن: {str(e)}'
            }

class AramexService(DeliveryServiceInterface):
    """خدمة التكامل مع Aramex"""
    
    def __init__(self):
        self.username = os.getenv('ARAMEX_USERNAME', '')
        self.password = os.getenv('ARAMEX_PASSWORD', '')
        self.account_number = os.getenv('ARAMEX_ACCOUNT_NUMBER', '')
        self.account_pin = os.getenv('ARAMEX_PIN', '')
        self.account_entity = os.getenv('ARAMEX_ENTITY', 'ALG')
        self.base_url = 'https://ws.aramex.net/ShippingAPI.V2/Shipping/Service_1_0.svc'
    
    def create_shipment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء شحنة جديدة في Aramex"""
        try:
            # تحضير بيانات المصادقة
            client_info = {
                'UserName': self.username,
                'Password': self.password,
                'Version': 'v1.0',
                'AccountNumber': self.account_number,
                'AccountPin': self.account_pin,
                'AccountEntity': self.account_entity,
                'AccountCountryCode': 'DZ',
                'Source': 24
            }
            
            # تحضير بيانات الشحنة
            shipment_data = {
                'ClientInfo': client_info,
                'Shipments': [{
                    'Reference1': order_data.get('order_id', ''),
                    'Reference2': '',
                    'Reference3': '',
                    'Shipper': {
                        'Reference1': '',
                        'Reference2': '',
                        'AccountNumber': self.account_number,
                        'PartyAddress': {
                            'Line1': order_data.get('sender_address', ''),
                            'City': order_data.get('sender_city', 'Algiers'),
                            'StateOrProvinceCode': '',
                            'PostCode': '',
                            'CountryCode': 'DZ'
                        },
                        'Contact': {
                            'Department': '',
                            'PersonName': order_data.get('sender_name', ''),
                            'Title': '',
                            'CompanyName': order_data.get('sender_company', ''),
                            'PhoneNumber1': order_data.get('sender_phone', ''),
                            'PhoneNumber1Ext': '',
                            'PhoneNumber2': '',
                            'PhoneNumber2Ext': '',
                            'FaxNumber': '',
                            'CellPhone': order_data.get('sender_phone', ''),
                            'EmailAddress': order_data.get('sender_email', ''),
                            'Type': ''
                        }
                    },
                    'Consignee': {
                        'Reference1': '',
                        'Reference2': '',
                        'AccountNumber': '',
                        'PartyAddress': {
                            'Line1': order_data.get('customer_address', ''),
                            'City': order_data.get('customer_city', ''),
                            'StateOrProvinceCode': '',
                            'PostCode': '',
                            'CountryCode': 'DZ'
                        },
                        'Contact': {
                            'Department': '',
                            'PersonName': order_data.get('customer_name', ''),
                            'Title': '',
                            'CompanyName': '',
                            'PhoneNumber1': order_data.get('customer_phone', ''),
                            'PhoneNumber1Ext': '',
                            'PhoneNumber2': '',
                            'PhoneNumber2Ext': '',
                            'FaxNumber': '',
                            'CellPhone': order_data.get('customer_phone', ''),
                            'EmailAddress': order_data.get('customer_email', ''),
                            'Type': ''
                        }
                    },
                    'ShippingDateTime': order_data.get('shipping_date', ''),
                    'DueDate': order_data.get('due_date', ''),
                    'Comments': order_data.get('comments', ''),
                    'PickupLocation': 'Reception',
                    'OperationsInstructions': '',
                    'AccountingInstrcutions': '',
                    'Details': {
                        'Dimensions': {
                            'Length': order_data.get('length', 10),
                            'Width': order_data.get('width', 10),
                            'Height': order_data.get('height', 10),
                            'Unit': 'CM'
                        },
                        'ActualWeight': {
                            'Value': order_data.get('weight', 1),
                            'Unit': 'KG'
                        },
                        'ProductGroup': 'EXP',
                        'ProductType': 'PDX',
                        'PaymentType': 'P',
                        'PaymentOptions': '',
                        'Services': '',
                        'NumberOfPieces': 1,
                        'DescriptionOfGoods': order_data.get('product_description', ''),
                        'GoodsOriginCountry': 'DZ'
                    }
                }],
                'LabelInfo': {
                    'ReportID': 9201,
                    'ReportType': 'URL'
                }
            }
            
            # إرسال الطلب
            response = requests.post(
                f'{self.base_url}/json/CreateShipments',
                json=shipment_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('HasErrors', True):
                    return {
                        'success': False,
                        'message': f'خطأ من Aramex: {result.get("Notifications", [])}',
                        'data': result
                    }
                else:
                    shipment_result = result.get('Shipments', [{}])[0]
                    return {
                        'success': True,
                        'tracking_number': shipment_result.get('ID', ''),
                        'reference': shipment_result.get('Reference1', ''),
                        'label_url': result.get('LabelURL', ''),
                        'message': 'تم إنشاء الشحنة بنجاح',
                        'data': result
                    }
            else:
                return {
                    'success': False,
                    'message': f'فشل في إنشاء الشحنة: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إنشاء الشحنة: {str(e)}'
            }
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """تتبع الشحنة في Aramex"""
        try:
            client_info = {
                'UserName': self.username,
                'Password': self.password,
                'Version': 'v1.0',
                'AccountNumber': self.account_number,
                'AccountPin': self.account_pin,
                'AccountEntity': self.account_entity,
                'AccountCountryCode': 'DZ',
                'Source': 24
            }
            
            tracking_data = {
                'ClientInfo': client_info,
                'Shipments': [tracking_number],
                'GetLastTrackingUpdateOnly': False
            }
            
            response = requests.post(
                f'{self.base_url}/json/TrackShipments',
                json=tracking_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get('HasErrors', True):
                    tracking_results = result.get('TrackingResults', [])
                    if tracking_results:
                        tracking_result = tracking_results[0]
                        return {
                            'success': True,
                            'tracking_number': tracking_number,
                            'status': tracking_result.get('UpdateDescription', ''),
                            'last_update': tracking_result.get('UpdateDateTime', ''),
                            'location': tracking_result.get('UpdateLocation', ''),
                            'tracking_history': result.get('TrackingResults', []),
                            'data': result
                        }
                
                return {
                    'success': False,
                    'message': f'خطأ في تتبع الشحنة: {result.get("Notifications", [])}',
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'message': f'فشل في تتبع الشحنة: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تتبع الشحنة: {str(e)}'
            }
    
    def cancel_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """إلغاء الشحنة في Aramex (غير متاح في API العام)"""
        return {
            'success': False,
            'message': 'إلغاء الشحنة غير متاح في Aramex API العام'
        }
    
    def get_shipping_cost(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب تكلفة الشحن في Aramex"""
        try:
            client_info = {
                'UserName': self.username,
                'Password': self.password,
                'Version': 'v1.0',
                'AccountNumber': self.account_number,
                'AccountPin': self.account_pin,
                'AccountEntity': self.account_entity,
                'AccountCountryCode': 'DZ',
                'Source': 24
            }
            
            rate_data = {
                'ClientInfo': client_info,
                'OriginAddress': {
                    'Line1': order_data.get('sender_address', ''),
                    'City': order_data.get('sender_city', 'Algiers'),
                    'StateOrProvinceCode': '',
                    'PostCode': '',
                    'CountryCode': 'DZ'
                },
                'DestinationAddress': {
                    'Line1': order_data.get('customer_address', ''),
                    'City': order_data.get('customer_city', ''),
                    'StateOrProvinceCode': '',
                    'PostCode': '',
                    'CountryCode': 'DZ'
                },
                'ShipmentDetails': {
                    'Dimensions': {
                        'Length': order_data.get('length', 10),
                        'Width': order_data.get('width', 10),
                        'Height': order_data.get('height', 10),
                        'Unit': 'CM'
                    },
                    'ActualWeight': {
                        'Value': order_data.get('weight', 1),
                        'Unit': 'KG'
                    },
                    'ProductGroup': 'EXP',
                    'ProductType': 'PDX',
                    'PaymentType': 'P',
                    'PaymentOptions': '',
                    'Services': '',
                    'NumberOfPieces': 1,
                    'DescriptionOfGoods': order_data.get('product_description', ''),
                    'GoodsOriginCountry': 'DZ'
                }
            }
            
            response = requests.post(
                f'{self.base_url}/json/CalculateRate',
                json=rate_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get('HasErrors', True):
                    total_amount = result.get('TotalAmount', {})
                    return {
                        'success': True,
                        'currency': total_amount.get('CurrencyCode', 'DZD'),
                        'total_cost': total_amount.get('Value', 0),
                        'data': result
                    }
                else:
                    return {
                        'success': False,
                        'message': f'خطأ في حساب التكلفة: {result.get("Notifications", [])}',
                        'data': result
                    }
            else:
                return {
                    'success': False,
                    'message': f'فشل في حساب تكلفة الشحن: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في حساب تكلفة الشحن: {str(e)}'
            }

class DeliveryServiceFactory:
    """مصنع لإنشاء خدمات التوصيل المختلفة"""
    
    @staticmethod
    def create_service(service_name: str) -> Optional[DeliveryServiceInterface]:
        """إنشاء خدمة التوصيل المطلوبة"""
        services = {
            'yalidine': YalidineService,
            'aramex': AramexService
        }
        
        service_class = services.get(service_name.lower())
        if service_class:
            return service_class()
        else:
            raise ValueError(f'خدمة التوصيل {service_name} غير مدعومة')

class DeliveryManager:
    """مدير عام لجميع خدمات التوصيل"""
    
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, service: DeliveryServiceInterface):
        """تسجيل خدمة توصيل جديدة"""
        self.services[name] = service
    
    def get_service(self, name: str) -> Optional[DeliveryServiceInterface]:
        """الحصول على خدمة توصيل محددة"""
        return self.services.get(name)
    
    def get_available_services(self) -> list:
        """الحصول على قائمة بجميع الخدمات المتاحة"""
        return list(self.services.keys())
    
    def create_shipment_with_service(self, service_name: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء شحنة باستخدام خدمة محددة"""
        service = self.get_service(service_name)
        if service:
            return service.create_shipment(order_data)
        else:
            return {
                'success': False,
                'message': f'خدمة التوصيل {service_name} غير متاحة'
            }
    
    def track_shipment_with_service(self, service_name: str, tracking_number: str) -> Dict[str, Any]:
        """تتبع شحنة باستخدام خدمة محددة"""
        service = self.get_service(service_name)
        if service:
            return service.track_shipment(tracking_number)
        else:
            return {
                'success': False,
                'message': f'خدمة التوصيل {service_name} غير متاحة'
            }

