from core.database import db_manager
from flask import render_template, request, Blueprint
from libraries import jdatetime
import time
from libraries import superuser_id

financial_bp = Blueprint('financial', __name__, url_prefix='/financial')

@financial_bp.route('/view')
def financial_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    # نمایش تراکنش‌ها همراه با نام مخاطب
    cursor.execute('''
        SELECT f.id, f.contact, c.name as contact_name, f.amount, f.date
        FROM financial f
        JOIN contact c ON f.contact = c.id
        ORDER BY f.date DESC
    ''')
    transactions = cursor.fetchall()
    conn.close()
    
    # تبدیل timestamp به شمسی برای هر رکورد
    trans_list = []
    for t in transactions:
        # تبدیل Unix timestamp به datetime شمسی
        jalali_date = jdatetime.datetime.fromtimestamp(t['date']).strftime("%Y/%m/%d")
        trans_list.append({
            'id': t['id'],
            'contact': t['contact'],
            'contact_name': t['contact_name'],
            'amount': t['amount'],
            'date_shamsi': jalali_date,
            'timestamp': t['date']
        })
    return render_template('financial_list.html', transactions=trans_list)

@financial_bp.route('/add', methods=['GET', 'POST'])
def financial_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        contact_id = request.form.get('contact')
        amount_str = request.form.get('amount')
        transaction_type = request.form.get('transaction_type')  # 'receive' یا 'pay'
        description = request.form.get('description', '').strip()
        
        if not amount_str:
            return "مبلغ الزامی است. <a href='/financial/add'>بازگشت</a>"
        
        amount = int(amount_str)
        if amount < 0:
            return "مبلغ باید مثبت باشد. <a href='/financial/add'>بازگشت</a>"
        
        # تعیین علامت
        if transaction_type == 'receive':
            final_amount = amount   # دریافت: مثبت
        elif transaction_type == 'pay':
            final_amount = -amount  # پرداخت: منفی
        else:
            return "نوع تراکنش نامعتبر است. <a href='/financial/add'>بازگشت</a>"
        
        current_timestamp = int(time.time())
        
        cursor.execute('''
            INSERT INTO financial (contact, amount, date, description)
            VALUES (?, ?, ?, ?)
        ''', (contact_id, final_amount, current_timestamp, description))
        cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (final_amount, contact_id))
        cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (final_amount, superuser_id))

        conn.commit()
        conn.close()
        return '<h3>تراکنش مالی با موفقیت ثبت شد.</h3><a href="/financial/view">بازگشت به لیست تراکنش‌ها</a>'
    
    else:
        cursor.execute('SELECT id, name FROM contact WHERE id != ? ORDER BY name', (superuser_id,))
        contacts = cursor.fetchall()
        conn.close()
        return render_template('financial_form.html', contacts=contacts)