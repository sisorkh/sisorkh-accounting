from core.database import db_manager
from flask import render_template, request, Blueprint
from libraries import jdatetime
import isbnlib

goods_bp = Blueprint('goods', __name__, url_prefix='/goods')

@goods_bp.route('/view')
def goods_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    # نمایش کالاها همراه با نام کتاب
    cursor.execute('''
        SELECT g.id, b.name as book_name, g.isbn, g.cover, g.size, g.number, g.tirage, g.page, g.weight, g.year, g.status, g.sold, g.print
        FROM goods g
        JOIN book b ON g.book = b.id
        ORDER BY g.id DESC
    ''')
    goods_list = cursor.fetchall()
    conn.close()
    return render_template('goods_list.html', goods=goods_list)

@goods_bp.route('/add', methods=['GET', 'POST'])
def goods_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # دریافت اطلاعات
        book_id = request.form.get('book')
        isbn = request.form.get('isbn', '').strip()
        cover = request.form.get('cover')
        size = request.form.get('size')
        number = request.form.get('number') or None
        tirage = request.form.get('tirage') or None
        page = request.form.get('page') or None
        weight = request.form.get('weight') or None
        year = request.form.get('year')
        
        # اعتبارسنجی ISBN (اگر خالی نباشد)
        if isbn:
            if not isbnlib.is_isbn13(isbn):
                conn.close()
                return "خطا: شابک وارد شده معتبر نیست (باید 13 رقمی باشد). <a href='/goods/add'>بازگشت</a>"
        
        # مقداردهی پیش‌فرض
        status = 1
        sold = 0
        print = 0
        
        # درج در دیتابیس
        cursor.execute('''
            INSERT INTO goods (book, isbn, cover, size, number, tirage, page, weight, year, status, sold, print)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (book_id, isbn, cover, size, number, tirage, page, weight, year, status, sold, print))
        
        conn.commit()
        conn.close()
        return f'<h3>کالا با موفقیت اضافه شد.</h3><a href="/goods/view">بازگشت به لیست کالاها</a>'
    
    else:
        # دریافت لیست کتاب‌ها (برای انتخاب)
        cursor.execute('SELECT id, name, second FROM book ORDER BY name')
        books = cursor.fetchall()
        conn.close()
        default_year = jdatetime.datetime.now().year
        return render_template('goods_form.html', books=books, default_year=default_year)