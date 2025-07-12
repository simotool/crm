from flask import Blueprint, request, jsonify
from src.models import db, DeliveryCompany

delivery_company_bp = Blueprint('delivery_company', __name__)

@delivery_company_bp.route('/delivery-companies', methods=['GET'])
def get_delivery_companies():
    """جلب جميع شركات التوصيل"""
    try:
        companies = DeliveryCompany.query.all()
        return jsonify({
            'success': True,
            'data': [company.to_dict() for company in companies]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب شركات التوصيل: {str(e)}'
        }), 500

@delivery_company_bp.route('/delivery-companies/<int:company_id>', methods=['GET'])
def get_delivery_company(company_id):
    """جلب شركة توصيل محددة"""
    try:
        company = DeliveryCompany.query.get(company_id)
        if not company:
            return jsonify({
                'success': False,
                'message': 'شركة التوصيل غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'data': company.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب شركة التوصيل: {str(e)}'
        }), 500

@delivery_company_bp.route('/delivery-companies', methods=['POST'])
def create_delivery_company():
    """إنشاء شركة توصيل جديدة"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['company_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # إنشاء شركة التوصيل الجديدة
        company = DeliveryCompany(
            company_name=data['company_name'],
            api_endpoint=data.get('api_endpoint', ''),
            api_key=data.get('api_key', ''),
            contact_person=data.get('contact_person', ''),
            contact_phone=data.get('contact_phone', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(company)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء شركة التوصيل بنجاح',
            'data': company.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء شركة التوصيل: {str(e)}'
        }), 500

@delivery_company_bp.route('/delivery-companies/<int:company_id>', methods=['PUT'])
def update_delivery_company(company_id):
    """تحديث شركة توصيل"""
    try:
        company = DeliveryCompany.query.get(company_id)
        if not company:
            return jsonify({
                'success': False,
                'message': 'شركة التوصيل غير موجودة'
            }), 404
        
        data = request.get_json()
        
        # تحديث البيانات
        if 'company_name' in data:
            company.company_name = data['company_name']
        if 'api_endpoint' in data:
            company.api_endpoint = data['api_endpoint']
        if 'api_key' in data:
            company.api_key = data['api_key']
        if 'contact_person' in data:
            company.contact_person = data['contact_person']
        if 'contact_phone' in data:
            company.contact_phone = data['contact_phone']
        if 'is_active' in data:
            company.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث شركة التوصيل بنجاح',
            'data': company.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث شركة التوصيل: {str(e)}'
        }), 500

@delivery_company_bp.route('/delivery-companies/<int:company_id>', methods=['DELETE'])
def delete_delivery_company(company_id):
    """حذف شركة توصيل"""
    try:
        company = DeliveryCompany.query.get(company_id)
        if not company:
            return jsonify({
                'success': False,
                'message': 'شركة التوصيل غير موجودة'
            }), 404
        
        db.session.delete(company)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف شركة التوصيل بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف شركة التوصيل: {str(e)}'
        }), 500

