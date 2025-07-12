from flask import Blueprint, request, jsonify
from src.models import db, Expense
from datetime import datetime, timedelta
from sqlalchemy import func

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/expenses', methods=['GET'])
def get_expenses():
    """جلب جميع المصاريف"""
    try:
        # إمكانية التصفية
        expense_type = request.args.get('expense_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        query = Expense.query
        
        # تطبيق المرشحات
        if expense_type:
            query = query.filter_by(expense_type=expense_type)
        
        if start_date:
            start_date_obj = datetime.fromisoformat(start_date)
            query = query.filter(Expense.expense_date >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.fromisoformat(end_date)
            query = query.filter(Expense.expense_date <= end_date_obj)
        
        # ترتيب حسب التاريخ (الأحدث أولاً)
        query = query.order_by(Expense.expense_date.desc())
        
        # تطبيق التصفح
        expenses = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [expense.to_dict() for expense in expenses.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': expenses.total,
                'pages': expenses.pages,
                'has_next': expenses.has_next,
                'has_prev': expenses.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المصاريف: {str(e)}'
        }), 500

@expense_bp.route('/expenses/<int:expense_id>', methods=['GET'])
def get_expense(expense_id):
    """جلب مصروف محدد"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({
                'success': False,
                'message': 'المصروف غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': expense.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المصروف: {str(e)}'
        }), 500

@expense_bp.route('/expenses', methods=['POST'])
def create_expense():
    """إنشاء مصروف جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['expense_type', 'amount', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # التحقق من نوع المصروف
        valid_expense_types = ['إعلانات', 'عمال تأكيد', 'تغليف', 'مصاريف ثابتة', 'إرجاع طلبيات', 'أخرى']
        if data['expense_type'] not in valid_expense_types:
            return jsonify({
                'success': False,
                'message': f'نوع المصروف يجب أن يكون أحد القيم التالية: {", ".join(valid_expense_types)}'
            }), 400
        
        # إنشاء المصروف الجديد
        expense = Expense(
            expense_type=data['expense_type'],
            amount=float(data['amount']),
            description=data['description'],
            expense_date=datetime.fromisoformat(data['expense_date']) if 'expense_date' in data else datetime.utcnow(),
            order_id=data.get('order_id'),
            staff_id=data.get('staff_id')
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء المصروف بنجاح',
            'data': expense.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء المصروف: {str(e)}'
        }), 500

@expense_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """تحديث مصروف"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({
                'success': False,
                'message': 'المصروف غير موجود'
            }), 404
        
        data = request.get_json()
        
        # تحديث البيانات
        if 'expense_type' in data:
            valid_expense_types = ['إعلانات', 'عمال تأكيد', 'تغليف', 'مصاريف ثابتة', 'إرجاع طلبيات', 'أخرى']
            if data['expense_type'] not in valid_expense_types:
                return jsonify({
                    'success': False,
                    'message': f'نوع المصروف يجب أن يكون أحد القيم التالية: {", ".join(valid_expense_types)}'
                }), 400
            expense.expense_type = data['expense_type']
        
        if 'amount' in data:
            expense.amount = float(data['amount'])
        
        if 'description' in data:
            expense.description = data['description']
        
        if 'expense_date' in data:
            expense.expense_date = datetime.fromisoformat(data['expense_date'])
        
        if 'order_id' in data:
            expense.order_id = data['order_id']
        
        if 'staff_id' in data:
            expense.staff_id = data['staff_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث المصروف بنجاح',
            'data': expense.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث المصروف: {str(e)}'
        }), 500

@expense_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """حذف مصروف"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({
                'success': False,
                'message': 'المصروف غير موجود'
            }), 404
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف المصروف بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف المصروف: {str(e)}'
        }), 500

@expense_bp.route('/expenses/summary', methods=['GET'])
def get_expenses_summary():
    """جلب ملخص المصاريف"""
    try:
        # فترة التقرير
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # إذا لم تحدد الفترة، استخدم الشهر الحالي
        if not start_date or not end_date:
            now = datetime.utcnow()
            start_date = now.replace(day=1).isoformat()
            end_date = now.isoformat()
        
        start_date_obj = datetime.fromisoformat(start_date)
        end_date_obj = datetime.fromisoformat(end_date)
        
        # جلب المصاريف في الفترة المحددة
        expenses_query = Expense.query.filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        )
        
        # إجمالي المصاريف
        total_expenses = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        ).scalar() or 0
        
        # المصاريف حسب النوع
        expenses_by_type = db.session.query(
            Expense.expense_type,
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.expense_id).label('count')
        ).filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        ).group_by(Expense.expense_type).all()
        
        # تحويل النتائج إلى قاموس
        expenses_breakdown = []
        for expense_type, total_amount, count in expenses_by_type:
            expenses_breakdown.append({
                'expense_type': expense_type,
                'total_amount': float(total_amount),
                'count': count,
                'percentage': (float(total_amount) / total_expenses * 100) if total_expenses > 0 else 0
            })
        
        # ترتيب حسب المبلغ (الأعلى أولاً)
        expenses_breakdown.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_expenses': float(total_expenses),
                'expenses_breakdown': expenses_breakdown,
                'total_transactions': sum(item['count'] for item in expenses_breakdown)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب ملخص المصاريف: {str(e)}'
        }), 500

@expense_bp.route('/expenses/bulk', methods=['POST'])
def create_bulk_expenses():
    """إنشاء عدة مصاريف دفعة واحدة"""
    try:
        data = request.get_json()
        
        if 'expenses' not in data:
            return jsonify({
                'success': False,
                'message': 'قائمة المصاريف مطلوبة'
            }), 400
        
        expenses_data = data['expenses']
        
        if not isinstance(expenses_data, list):
            return jsonify({
                'success': False,
                'message': 'المصاريف يجب أن تكون قائمة'
            }), 400
        
        created_expenses = []
        failed_expenses = []
        
        for expense_data in expenses_data:
            try:
                # التحقق من البيانات المطلوبة
                required_fields = ['expense_type', 'amount', 'description']
                for field in required_fields:
                    if field not in expense_data:
                        failed_expenses.append({
                            'data': expense_data,
                            'error': f'الحقل {field} مطلوب'
                        })
                        continue
                
                # إنشاء المصروف
                expense = Expense(
                    expense_type=expense_data['expense_type'],
                    amount=float(expense_data['amount']),
                    description=expense_data['description'],
                    expense_date=datetime.fromisoformat(expense_data['expense_date']) if 'expense_date' in expense_data else datetime.utcnow(),
                    order_id=expense_data.get('order_id'),
                    staff_id=expense_data.get('staff_id')
                )
                
                db.session.add(expense)
                created_expenses.append(expense)
                
            except Exception as e:
                failed_expenses.append({
                    'data': expense_data,
                    'error': str(e)
                })
        
        # حفظ المصاريف المنشأة بنجاح
        if created_expenses:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم إنشاء {len(created_expenses)} مصروف بنجاح، فشل في {len(failed_expenses)} مصروف',
            'created_count': len(created_expenses),
            'failed_count': len(failed_expenses),
            'created_expenses': [expense.to_dict() for expense in created_expenses],
            'failed_expenses': failed_expenses
        }), 201 if created_expenses else 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء المصاريف: {str(e)}'
        }), 500

