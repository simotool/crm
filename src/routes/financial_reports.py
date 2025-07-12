from flask import Blueprint, request, jsonify
from src.models import db, Order, Product, Expense, DeliveryPriceList
from datetime import datetime, timedelta
from sqlalchemy import func, and_

financial_reports_bp = Blueprint('financial_reports', __name__)

@financial_reports_bp.route('/financial/profit-loss', methods=['GET'])
def get_profit_loss_report():
    """تقرير الأرباح والخسائر"""
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
        
        # الطلبات المؤكدة والمسلمة في الفترة المحددة
        confirmed_orders = Order.query.filter(
            Order.order_date >= start_date_obj,
            Order.order_date <= end_date_obj,
            Order.order_status.in_(['مؤكد', 'تم الشحن', 'تم التسليم'])
        ).all()
        
        # حساب الإيرادات
        total_revenue = 0
        total_orders = len(confirmed_orders)
        total_quantity_sold = 0
        
        for order in confirmed_orders:
            if order.total_amount:
                total_revenue += float(order.total_amount)
            total_quantity_sold += order.quantity
        
        # حساب تكلفة البضاعة المباعة (COGS)
        total_cogs = 0
        for order in confirmed_orders:
            if order.product and order.product.cost_price:
                total_cogs += float(order.product.cost_price) * order.quantity
        
        # إجمالي المصاريف في الفترة
        total_expenses = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        ).scalar() or 0
        
        # تفصيل المصاريف حسب النوع
        expenses_by_type = db.session.query(
            Expense.expense_type,
            func.sum(Expense.amount).label('total_amount')
        ).filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        ).group_by(Expense.expense_type).all()
        
        expenses_breakdown = {}
        for expense_type, amount in expenses_by_type:
            expenses_breakdown[expense_type] = float(amount)
        
        # حساب الأرباح
        gross_profit = total_revenue - total_cogs  # الربح الإجمالي
        net_profit = gross_profit - float(total_expenses)  # الربح الصافي
        
        # نسب الربحية
        gross_profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        net_profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # متوسط قيمة الطلب
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'revenue': {
                    'total_revenue': total_revenue,
                    'total_orders': total_orders,
                    'total_quantity_sold': total_quantity_sold,
                    'average_order_value': average_order_value
                },
                'costs': {
                    'total_cogs': total_cogs,
                    'total_expenses': float(total_expenses),
                    'expenses_breakdown': expenses_breakdown
                },
                'profit': {
                    'gross_profit': gross_profit,
                    'net_profit': net_profit,
                    'gross_profit_margin': gross_profit_margin,
                    'net_profit_margin': net_profit_margin
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تقرير الأرباح والخسائر: {str(e)}'
        }), 500

@financial_reports_bp.route('/financial/product-profitability', methods=['GET'])
def get_product_profitability():
    """تقرير ربحية المنتجات"""
    try:
        # فترة التقرير
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            now = datetime.utcnow()
            start_date = now.replace(day=1).isoformat()
            end_date = now.isoformat()
        
        start_date_obj = datetime.fromisoformat(start_date)
        end_date_obj = datetime.fromisoformat(end_date)
        
        # جلب بيانات المبيعات حسب المنتج
        product_sales = db.session.query(
            Order.product_id,
            func.sum(Order.quantity).label('total_quantity'),
            func.sum(Order.total_amount).label('total_revenue'),
            func.count(Order.order_id).label('total_orders')
        ).filter(
            Order.order_date >= start_date_obj,
            Order.order_date <= end_date_obj,
            Order.order_status.in_(['مؤكد', 'تم الشحن', 'تم التسليم'])
        ).group_by(Order.product_id).all()
        
        product_profitability = []
        
        for product_id, total_quantity, total_revenue, total_orders in product_sales:
            product = Product.query.get(product_id)
            
            if not product:
                continue
            
            # حساب التكاليف
            total_cogs = float(product.cost_price or 0) * total_quantity
            
            # حساب مصاريف التوصيل (إذا كانت متاحة)
            delivery_costs = 0
            # يمكن إضافة حساب تكاليف التوصيل هنا إذا كانت متاحة
            
            # حساب الأرباح
            gross_profit = float(total_revenue or 0) - total_cogs
            net_profit = gross_profit - delivery_costs
            
            # نسب الربحية
            profit_margin = (net_profit / float(total_revenue or 1) * 100) if total_revenue else 0
            
            product_profitability.append({
                'product_id': product_id,
                'product_name': product.product_name,
                'sku': product.sku,
                'total_quantity_sold': total_quantity,
                'total_orders': total_orders,
                'total_revenue': float(total_revenue or 0),
                'total_cogs': total_cogs,
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'profit_margin': profit_margin,
                'average_order_value': float(total_revenue or 0) / total_orders if total_orders > 0 else 0
            })
        
        # ترتيب حسب الربح الصافي (الأعلى أولاً)
        product_profitability.sort(key=lambda x: x['net_profit'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'products': product_profitability,
                'total_products': len(product_profitability)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تقرير ربحية المنتجات: {str(e)}'
        }), 500

@financial_reports_bp.route('/financial/daily-summary', methods=['GET'])
def get_daily_financial_summary():
    """ملخص مالي يومي"""
    try:
        # التاريخ المطلوب (افتراضياً اليوم)
        target_date = request.args.get('date')
        
        if target_date:
            target_date_obj = datetime.fromisoformat(target_date)
        else:
            target_date_obj = datetime.utcnow()
            target_date = target_date_obj.isoformat()
        
        # بداية ونهاية اليوم
        start_of_day = target_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # الطلبات في هذا اليوم
        daily_orders = Order.query.filter(
            Order.order_date >= start_of_day,
            Order.order_date <= end_of_day
        ).all()
        
        # إحصائيات الطلبات
        total_orders = len(daily_orders)
        confirmed_orders = [o for o in daily_orders if o.order_status in ['مؤكد', 'تم الشحن', 'تم التسليم']]
        pending_orders = [o for o in daily_orders if o.order_status == 'جديد']
        cancelled_orders = [o for o in daily_orders if o.order_status == 'ملغي']
        
        # الإيرادات
        daily_revenue = sum(float(order.total_amount or 0) for order in confirmed_orders)
        
        # المصاريف اليومية
        daily_expenses = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.expense_date >= start_of_day,
            Expense.expense_date <= end_of_day
        ).scalar() or 0
        
        # الربح الصافي التقديري
        estimated_cogs = 0
        for order in confirmed_orders:
            if order.product and order.product.cost_price:
                estimated_cogs += float(order.product.cost_price) * order.quantity
        
        estimated_net_profit = daily_revenue - estimated_cogs - float(daily_expenses)
        
        # مقارنة مع اليوم السابق
        previous_day = start_of_day - timedelta(days=1)
        previous_day_end = end_of_day - timedelta(days=1)
        
        previous_orders = Order.query.filter(
            Order.order_date >= previous_day,
            Order.order_date <= previous_day_end,
            Order.order_status.in_(['مؤكد', 'تم الشحن', 'تم التسليم'])
        ).all()
        
        previous_revenue = sum(float(order.total_amount or 0) for order in previous_orders)
        
        # نسبة التغيير
        revenue_change = ((daily_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        orders_change = ((len(confirmed_orders) - len(previous_orders)) / len(previous_orders) * 100) if len(previous_orders) > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'date': target_date,
                'orders': {
                    'total_orders': total_orders,
                    'confirmed_orders': len(confirmed_orders),
                    'pending_orders': len(pending_orders),
                    'cancelled_orders': len(cancelled_orders),
                    'orders_change_percentage': orders_change
                },
                'financial': {
                    'daily_revenue': daily_revenue,
                    'daily_expenses': float(daily_expenses),
                    'estimated_cogs': estimated_cogs,
                    'estimated_net_profit': estimated_net_profit,
                    'revenue_change_percentage': revenue_change
                },
                'comparison': {
                    'previous_day_revenue': previous_revenue,
                    'previous_day_orders': len(previous_orders)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الملخص المالي اليومي: {str(e)}'
        }), 500

@financial_reports_bp.route('/financial/monthly-trend', methods=['GET'])
def get_monthly_financial_trend():
    """اتجاه الأرباح الشهرية"""
    try:
        # عدد الأشهر المطلوبة (افتراضياً 6 أشهر)
        months_count = int(request.args.get('months', 6))
        
        # تاريخ البداية
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months_count * 30)  # تقريبي
        
        monthly_data = []
        
        # حساب البيانات لكل شهر
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            # بداية ونهاية الشهر
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            month_end = next_month - timedelta(days=1)
            
            # الطلبات المؤكدة في هذا الشهر
            monthly_orders = Order.query.filter(
                Order.order_date >= current_date,
                Order.order_date <= month_end,
                Order.order_status.in_(['مؤكد', 'تم الشحن', 'تم التسليم'])
            ).all()
            
            # الإيرادات الشهرية
            monthly_revenue = sum(float(order.total_amount or 0) for order in monthly_orders)
            
            # المصاريف الشهرية
            monthly_expenses = db.session.query(
                func.sum(Expense.amount)
            ).filter(
                Expense.expense_date >= current_date,
                Expense.expense_date <= month_end
            ).scalar() or 0
            
            # تكلفة البضاعة المباعة
            monthly_cogs = 0
            for order in monthly_orders:
                if order.product and order.product.cost_price:
                    monthly_cogs += float(order.product.cost_price) * order.quantity
            
            # الربح الصافي
            monthly_net_profit = monthly_revenue - monthly_cogs - float(monthly_expenses)
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'month_name': current_date.strftime('%B %Y'),
                'total_orders': len(monthly_orders),
                'revenue': monthly_revenue,
                'expenses': float(monthly_expenses),
                'cogs': monthly_cogs,
                'net_profit': monthly_net_profit,
                'profit_margin': (monthly_net_profit / monthly_revenue * 100) if monthly_revenue > 0 else 0
            })
            
            # الانتقال للشهر التالي
            current_date = next_month
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'months_count': months_count
                },
                'monthly_trend': monthly_data
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في اتجاه الأرباح الشهرية: {str(e)}'
        }), 500

@financial_reports_bp.route('/financial/expense-analysis', methods=['GET'])
def get_expense_analysis():
    """تحليل المصاريف التفصيلي"""
    try:
        # فترة التحليل
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            now = datetime.utcnow()
            start_date = now.replace(day=1).isoformat()
            end_date = now.isoformat()
        
        start_date_obj = datetime.fromisoformat(start_date)
        end_date_obj = datetime.fromisoformat(end_date)
        
        # إجمالي المصاريف
        total_expenses = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        ).scalar() or 0
        
        # المصاريف حسب النوع مع التفاصيل
        expenses_by_type = db.session.query(
            Expense.expense_type,
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.expense_id).label('count'),
            func.avg(Expense.amount).label('average_amount'),
            func.max(Expense.amount).label('max_amount'),
            func.min(Expense.amount).label('min_amount')
        ).filter(
            Expense.expense_date >= start_date_obj,
            Expense.expense_date <= end_date_obj
        ).group_by(Expense.expense_type).all()
        
        expense_analysis = []
        for expense_type, total_amount, count, avg_amount, max_amount, min_amount in expenses_by_type:
            expense_analysis.append({
                'expense_type': expense_type,
                'total_amount': float(total_amount),
                'count': count,
                'average_amount': float(avg_amount),
                'max_amount': float(max_amount),
                'min_amount': float(min_amount),
                'percentage_of_total': (float(total_amount) / float(total_expenses) * 100) if total_expenses > 0 else 0
            })
        
        # ترتيب حسب المبلغ الإجمالي
        expense_analysis.sort(key=lambda x: x['total_amount'], reverse=True)
        
        # المصاريف اليومية (آخر 30 يوم)
        daily_expenses = []
        for i in range(30):
            day = end_date_obj - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_total = db.session.query(
                func.sum(Expense.amount)
            ).filter(
                Expense.expense_date >= day_start,
                Expense.expense_date <= day_end
            ).scalar() or 0
            
            daily_expenses.append({
                'date': day.strftime('%Y-%m-%d'),
                'total_expenses': float(day_total)
            })
        
        # ترتيب حسب التاريخ (الأقدم أولاً)
        daily_expenses.reverse()
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_expenses': float(total_expenses),
                    'total_transactions': sum(item['count'] for item in expense_analysis),
                    'average_expense_per_transaction': float(total_expenses) / sum(item['count'] for item in expense_analysis) if sum(item['count'] for item in expense_analysis) > 0 else 0
                },
                'expense_breakdown': expense_analysis,
                'daily_trend': daily_expenses
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحليل المصاريف: {str(e)}'
        }), 500

