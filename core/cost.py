from core.database import db_manager
from flask import render_template, request, Blueprint
from libraries import jdatetime
import time
from libraries import superuser_id

cost_bp = Blueprint('cost', __name__, url_prefix='/cost')

@cost_bp.route('/view')
def cost_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.book, c.description, c.amount, c.date,
               COALESCE(b.name, 'هزینه‌ی کلی') as book_name
        FROM cost c
        LEFT JOIN book b ON c.book = b.id
        ORDER BY c.date DESC
    ''')
    costs = cursor.fetchall()
    conn.close()
    
    cost_list = []
    for row in costs:
        jalali_date = jdatetime.datetime.fromtimestamp(row['date']).strftime("%Y/%m/%d")
        cost_list.append({
            'id': row['id'],
            'book_id': row['book'],
            'book_name': row['book_name'],
            'description': row['description'],
            'amount': row['amount'],
            'date_shamsi': jalali_date,
            'timestamp': row['date']
        })
    return render_template('cost_list.html', costs=cost_list)

@cost_bp.route('/add', methods=['GET', 'POST'])
def cost_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        book_id = request.form.get('book')
        description = request.form.get('description', '').strip()
        amount_str = request.form.get('amount')
        cost_type = request.form.get('cost_type')  # 'receive' یا 'pay'
        
        if not book_id:
            return "انتخاب کتاب الزامی است. <a href='/cost/add'>بازگشت</a>"
        if not amount_str:
            return "مبلغ الزامی است. <a href='/cost/add'>بازگشت</a>"
        
        amount = int(amount_str)
        if amount < 0:
            return "مبلغ باید مثبت وارد شود. <a href='/cost/add'>بازگشت</a>"
        
        if cost_type == 'receive':
            final_amount = amount   # دریافت: مثبت
        elif cost_type == 'pay':
            final_amount = -amount  # پرداخت: منفی
        else:
            return "نوع هزینه نامعتبر است. <a href='/cost/add'>بازگشت</a>"
        
        current_timestamp = int(time.time())
        total_share = 0
        cursor.execute('''
            INSERT INTO cost (book, description, amount, date)
            VALUES (?, ?, ?, ?)
        ''', (book_id, description, final_amount, current_timestamp))

        # دریافت سهام‌داران کتاب
        if book_id != '0':
            cursor.execute('SELECT contact, share FROM share WHERE book = ?', (book_id,))
            shares = cursor.fetchall()

            if shares:
                for sh in shares:
                    total_share += sh['share']
                    share_amount = int(final_amount * (sh['share'] / 100.0))
                    cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (share_amount, sh['contact']))
    
        #سهم سوپر یوزر
        net = 100 - total_share
        if net:
            share_amount = int(final_amount * (net / 100.0))
            cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (share_amount, superuser_id))

        conn.commit()
        conn.close()
        return '<h3>هزینه با موفقیت ثبت شد.</h3><a href="/cost/view">بازگشت به لیست هزینه‌ها</a>'
    
    else:
        cursor.execute('SELECT id, name, second FROM book ORDER BY name')
        books = cursor.fetchall()
        conn.close()
        return render_template('cost_form.html', books=books)