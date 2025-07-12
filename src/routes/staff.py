from flask import Blueprint, request, jsonify
from src.models import db, Staff

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/staff', methods=['GET'])
def get_staff():
    """جلب جميع الموظفين"""
    try:
        # إمكانية التصفية حسب الدور
        role = request.args.get('role')
        is_active = request.args.get('is_active')
        
        query = Staff.query
        
        if role:
            query = query.filter_by(role=role)
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        staff_members = query.all()
        
        return jsonify({
            'success': True,
            'data': [staff.to_dict() for staff in staff_members]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الموظفين: {str(e)}'
        }), 500

@staff_bp.route('/staff/<int:staff_id>', methods=['GET'])
def get_staff_member(staff_id):
    """جلب موظف محدد"""
    try:
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': staff.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الموظف: {str(e)}'
        }), 500

@staff_bp.route('/staff', methods=['POST'])
def create_staff():
    """إنشاء موظف جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['staff_name', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # إنشاء الموظف الجديد
        staff = Staff(
            staff_name=data['staff_name'],
            role=data['role'],
            contact_phone=data.get('contact_phone', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(staff)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء الموظف بنجاح',
            'data': staff.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الموظف: {str(e)}'
        }), 500

@staff_bp.route('/staff/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    """تحديث موظف"""
    try:
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        data = request.get_json()
        
        # تحديث البيانات
        if 'staff_name' in data:
            staff.staff_name = data['staff_name']
        if 'role' in data:
            staff.role = data['role']
        if 'contact_phone' in data:
            staff.contact_phone = data['contact_phone']
        if 'is_active' in data:
            staff.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الموظف بنجاح',
            'data': staff.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث الموظف: {str(e)}'
        }), 500

@staff_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    """حذف موظف"""
    try:
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        db.session.delete(staff)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الموظف بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف الموظف: {str(e)}'
        }), 500

@staff_bp.route('/staff/<int:staff_id>/orders', methods=['GET'])
def get_staff_orders(staff_id):
    """جلب الطلبات المخصصة لموظف معين"""
    try:
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        # جلب الطلبات المخصصة لهذا الموظف
        orders = staff.orders
        
        return jsonify({
            'success': True,
            'data': {
                'staff': staff.to_dict(),
                'orders': [order.to_dict() for order in orders],
                'total_orders': len(orders)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب طلبات الموظف: {str(e)}'
        }), 500

