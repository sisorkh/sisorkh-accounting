from core.database import db_manager
from flask import render_template, request, Blueprint
from libraries import jdatetime

book_bp = Blueprint('book', __name__, url_prefix='/book')

@book_bp.route('/view')
def book_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    # لیست کتاب‌ها به همراه جمع سهم‌ها (اختیاری)
    cursor.execute('''
        SELECT b.id, b.name, b.second, b.year, b.print, b.electronic, b.audio, b.pod, b.share_type,
               (SELECT COALESCE(SUM(share),0) FROM share WHERE book = b.id) as total_share
        FROM book b
        ORDER BY b.id DESC
    ''')
    books = cursor.fetchall()
    conn.close()
    return render_template('book_list.html', books=books)

@book_bp.route('/add', methods=['GET', 'POST'])
def book_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # دریافت اطلاعات کتاب
        name = request.form.get('name')
        second = request.form.get('second')
        year = request.form.get('year')
        share_type = int(request.form.get('share_type'))
        
        if not name:
            return "عنوان کتاب الزامی است. <a href='/book/add'>بازگشت</a>"
        
        # درج کتاب
        cursor.execute('''
            INSERT INTO book (name, second, year, print, electronic, audio, pod, share_type)
            VALUES (?, ?, ?, 0, 0, 0, 0, ?)
        ''', (name, second, year, share_type))
        book_id = cursor.lastrowid
        
        # دریافت سهم‌ها از فرم (لیست دینامیک)
        # فرم باید شامل فیلدهای contact_ids[] و shares[] باشد
        contact_ids = request.form.getlist('contact_id[]')
        shares = request.form.getlist('share[]')
        
        # برای سود خالص و پشت جلد
        if share_type in (0, 1):
            total_share = 0
            for i in range(len(contact_ids)):
                if contact_ids[i] and shares[i]:
                    contact_id = int(contact_ids[i])
                    share_val = float(shares[i])
                    total_share += share_val
                    cursor.execute('''
                        INSERT INTO share (book, contact, share)
                        VALUES (?, ?, ?)
                    ''', (book_id, contact_id, share_val))
            
            # اعتبارسنجی نهایی مجموع سهم
            if total_share > 100:
                conn.rollback()
                conn.close()
                return f"خطا: مجموع سهم‌ها ({total_share}) بیشتر از ۱۰۰ است. لطفاً اصلاح کنید. <a href='/book/add'>بازگشت</a>"
        
        # برای یکجا
        elif share_type == 2:
            for i in range(len(contact_ids)):
                if contact_ids[i] and shares[i]:
                    contact_id = int(contact_ids[i])
                    share_val = int(shares[i])
                    cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (share_val, contact_id))
        
        conn.commit()
        conn.close()
        return f'<h3>کتاب "{name}" با موفقیت اضافه شد.</h3><a href="/book/view">بازگشت به لیست کتاب‌ها</a>'
    
    else:
        # دریافت لیست مخاطبان (برای انتخاب مؤلف)
        cursor.execute('SELECT id, name FROM contact ORDER BY name')
        contacts = cursor.fetchall()
        conn.close()
        # مقدار پیش‌فرض سال
        default_year = jdatetime.datetime.now().year
        return render_template('book_form.html', contacts=contacts, default_year=default_year)