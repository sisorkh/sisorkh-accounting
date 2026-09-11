from core.database import db_manager
from flask import render_template, request, Blueprint
from libraries import jdatetime
from libraries import company_info, superuser_id
import time

purchase_bp = Blueprint('purchase', __name__, url_prefix='/purchase')

@purchase_bp.route('/view')
def purchase_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.id, i.contact, c.name as contact_name, i.werehouse, i.description, 
               i.date, i.shipping_method, i.shipping_cost, i.final,
               (SELECT COUNT(*) FROM purchase_details WHERE purchase=i.id) as items_count
        FROM purchase i
        JOIN contact c ON i.contact = c.id
        ORDER BY i.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    purchases = []
    for row in rows:
        shamsi_date = jdatetime.datetime.fromtimestamp(row['date']).strftime("%Y/%m/%d")
        purchases.append({
            'id': row['id'],
            'contact_name': row['contact_name'],
            'werehouse': row['werehouse'],
            'date_shamsi': shamsi_date,
            'final': row['final'],
            'items_count': row['items_count']
        })
    return render_template('purchase_list.html', purchases=purchases)

@purchase_bp.route('/add', methods=['GET', 'POST'])
def purchase_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        contact_id = request.form.get('contact')
        warehouse_id = request.form.get('warehouse')
        description = request.form.get('description', '')
        shipping_method = request.form.get('shipping_method')
        shipping_cost = int(request.form.get('shipping_cost') or 0)
        final = 1 if request.form.get('final') == 'on' else 0
        
        if not contact_id or not warehouse_id:
            return "مخاطب و انبار الزامی است. <a href='/purchase/add'>بازگشت</a>"
        
        goods_ids = request.form.getlist('goods_id[]')
        numbers = request.form.getlist('number[]')
        prices = request.form.getlist('price[]')
        discounts = request.form.getlist('discount[]')
        new_prints = request.form.getlist('new_print[]')  # '1' یعنی این ردیف یک نوبت چاپ جدید است
        
        if not goods_ids:
            return "حداقل یک کالا باید انتخاب شود. <a href='/purchase/add'>بازگشت</a>"
        
        current_timestamp = int(time.time())
        current_year = jdatetime.datetime.now().year
        
        # درج در جدول purchase
        cursor.execute('''
            INSERT INTO purchase (contact, werehouse, description, date, shipping_method, shipping_cost, final)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (contact_id, warehouse_id, description, current_timestamp, shipping_method, shipping_cost, final))
        purchase_id = cursor.lastrowid
        
        total = shipping_cost
        register_payment = 1 if request.form.get('register_payment') == 'on' else 0

        for i in range(len(goods_ids)):
            goods_id = int(goods_ids[i])
            number = int(numbers[i])
            price = int(prices[i])
            discount_percent = int(discounts[i]) if discounts[i] else 0

            row_total = int(number * price * (1 - discount_percent / 100))
            total += row_total
            
            cursor.execute('''
                INSERT INTO purchase_details (purchase, goods, number, price, discount)
                VALUES (?, ?, ?, ?, ?)
            ''', (purchase_id, goods_id, number, price, discount_percent))
            
            # بروزرسانی جدول list (قیمت خرید)
            cursor.execute('SELECT id, buy FROM list WHERE goods = ?', (goods_id,))
            list_row = cursor.fetchone()
            if list_row:
                cursor.execute('UPDATE list SET buy = ?, date = ? WHERE goods = ?', (price, current_timestamp, goods_id))
            else:
                cursor.execute('INSERT INTO list (goods, buy, sell, date, sku) VALUES (?, ?, 0, ?, 0)', (goods_id, price, current_timestamp))
            
            # اگر فاکتور نهایی باشد، موجودی انبار را افزایش بده

            if final:
                # بروزرسانی موجودی انبار (stock)
                cursor.execute('SELECT id, number FROM stock WHERE goods = ? AND werehouse = ?', (goods_id, warehouse_id))
                stock_row = cursor.fetchone()
                if stock_row:
                    new_number = stock_row['number'] + number
                    cursor.execute('UPDATE stock SET number = ? WHERE id = ?', (new_number, stock_row['id']))
                else:
                    cursor.execute('INSERT INTO stock (goods, werehouse, number) VALUES (?, ?, ?)', (goods_id, warehouse_id, number))
                
                # بروزرسانی تعداد کل چاپ‌شده در جدول goods
                cursor.execute('UPDATE goods SET print = COALESCE(print, 0) + ? WHERE id = ?', (number, goods_id))
                
                # بروزرسانی نوبت‌های چاپ (prints)
                is_new_print = (i < len(new_prints)) and new_prints[i] == '1'
                cursor.execute('SELECT id, number FROM prints WHERE goods = ? ORDER BY number DESC LIMIT 1', (goods_id,))
                last_print = cursor.fetchone()
                if is_new_print or not last_print:
                    next_number = (last_print['number'] + 1) if last_print else 1
                    cursor.execute('''
                        INSERT INTO prints (goods, number, tirage, year)
                        VALUES (?, ?, ?, ?)
                    ''', (goods_id, next_number, number, current_year))
                else:
                    cursor.execute('UPDATE prints SET tirage = tirage + ? WHERE id = ?', (number, last_print['id']))

        if final and total:
            if register_payment:
                # ثبت در financial با مبلغ منفی
                cursor.execute('''
                    INSERT INTO financial (contact, amount, date)
                    VALUES (?, ?, ?)
                ''', (contact_id, -total, current_timestamp))
                
                # ضرر سوپر یوزر
                cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (-total, superuser_id))
            else:
                # فقط افزایش balance مخاطب (طلب بیشتر شده)
                cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (total, contact_id))        

        conn.commit()
        conn.close()
        return f'<h3>فاکتور خرید {"نهایی" if final else "پیش‌فاکتور"} با موفقیت ثبت شد.</h3><a href="/purchase/view">بازگشت به لیست خریدها</a>'
    
    else:
        cursor.execute('SELECT id, name FROM contact ORDER BY name')
        contacts = cursor.fetchall()
        cursor.execute('''
            SELECT w.id, c.name as contact_name 
            FROM warehouse w
            JOIN contact c ON w.contact = c.id
        ''')
        warehouses = cursor.fetchall()
        cursor.execute('''
            SELECT g.id, b.name as book_name, g.isbn, g.size
            FROM goods g
            JOIN book b ON g.book = b.id
            ORDER BY b.name
        ''')
        goods_list = cursor.fetchall()
        conn.close()
        return render_template('purchase_form.html', contacts=contacts, warehouses=warehouses, goods=goods_list)

@purchase_bp.route('/invoice/<int:invoice_id>')
def purchase_invoice(invoice_id):
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # اطلاعات اصلی فاکتور
    cursor.execute('''
        SELECT i.id, i.contact, i.werehouse, i.description, i.date, 
               i.shipping_method, i.shipping_cost, i.final,
               c.name as contact_name, c.type as contact_type, c.code as contact_code,
               c.address as contact_address, c.phone as contact_phone, 
               c.mobile as contact_mobile, c.postal as contact_postal, c.account as contact_account
        FROM purchase i
        JOIN contact c ON i.contact = c.id
        WHERE i.id = ?
    ''', (invoice_id,))
    invoice = cursor.fetchone()
    if not invoice:
        return "فاکتور یافت نشد.", 404
    
    # اطلاعات انبار
    cursor.execute('SELECT id FROM warehouse WHERE id = ?', (invoice['werehouse'],))
    warehouse = cursor.fetchone()
    
    # اقلام فاکتور همراه با جزئیات کالا، کتاب و کل چاپ شده

    cursor.execute('''
        SELECT d.id, d.number, d.price, d.discount,
            g.id as goods_id, g.isbn, g.cover, g.size, g.print as total_printed,
            b.name as book_name, b.second as book_second
        FROM purchase_details d
        JOIN goods g ON d.goods = g.id
        JOIN book b ON g.book = b.id
        WHERE d.purchase = ?
    ''', (invoice_id,))
    items = cursor.fetchall()
    conn.close()
    
    # محاسبه مبالغ
    subtotal = 0
    for item in items:
        item_total = item['number'] * item['price'] * (1 - item['discount'] / 100)
        subtotal += item_total
    total = subtotal + invoice['shipping_cost']
    
    # تبدیل تاریخ به شمسی
    date_shamsi = jdatetime.datetime.fromtimestamp(invoice['date']).strftime("%Y/%m/%d")
    
    # اطلاعات شرکت
    now = jdatetime.datetime.now()
    print_time = now.strftime("%H:%M:%S - %Y/%m/%d")
    
    return render_template('purchase_invoice.html',
                           invoice=invoice,
                           warehouse=warehouse,
                           items=items,
                           subtotal=subtotal,
                           total=total,
                           date_shamsi=date_shamsi,
                           company=company_info,
                           print_time=print_time)