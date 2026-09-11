from core.database import db_manager
from flask import render_template, request, Blueprint
import isbnlib

goods_bp = Blueprint('goods', __name__, url_prefix='/goods')

@goods_bp.route('/view')
def goods_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    # نمایش کالاها همراه با نام کتاب
    cursor.execute('''
        SELECT g.id, b.name as book_name, g.isbn, g.cover, g.size, g.page, g.weight, g.sold, g.print,
               p.number as last_print_number, p.tirage as last_print_tirage, p.year as last_print_year
        FROM goods g
        JOIN book b ON g.book = b.id
        LEFT JOIN prints p ON p.id = (
            SELECT id FROM prints WHERE goods = g.id ORDER BY number DESC LIMIT 1
        )
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
        page = request.form.get('page') or None
        weight = request.form.get('weight') or None
        
        # اعتبارسنجی ISBN (اگر خالی نباشد)
        if isbn:
            if not isbnlib.is_isbn13(isbn):
                conn.close()
                return "خطا: شابک وارد شده معتبر نیست (باید 13 رقمی باشد). <a href='/goods/add'>بازگشت</a>"
        
        # مقداردهی پیش‌فرض
        sold = 0
        goods_print = 0
        
        # درج در دیتابیس
        cursor.execute('''
            INSERT INTO goods (book, isbn, cover, size, page, weight, sold, print)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (book_id, isbn, cover, size, page, weight, sold, goods_print))
        
        conn.commit()
        conn.close()
        return f'<h3>کالا با موفقیت اضافه شد.</h3><a href="/goods/view">بازگشت به لیست کالاها</a>'
    
    else:
        # دریافت لیست کتاب‌ها (برای انتخاب)
        cursor.execute('SELECT id, name, second FROM book ORDER BY name')
        books = cursor.fetchall()
        conn.close()
        return render_template('goods_form.html', books=books)