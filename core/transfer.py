from core.database import db_manager
from flask import render_template, request, Blueprint
from libraries import jdatetime
import time
from libraries import company_info

transfer_bp = Blueprint('transfer', __name__, url_prefix='/transfer')

@transfer_bp.route('/view')
def transfer_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.werehouse as source_warehouse, t.status, t.date,
               (CASE WHEN t.status = -1 THEN 'فروش امانی' ELSE 'مرجوعی' END) as title,
               (SELECT COUNT(*) FROM transfer_details WHERE transfer=t.id) as items_count
        FROM transfer t
        ORDER BY t.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    transfers = []
    for row in rows:
        shamsi_date = jdatetime.datetime.fromtimestamp(row['date']).strftime("%Y/%m/%d")
        transfers.append({
            'id': row['id'],
            'source_warehouse': row['source_warehouse'],
            'status': row['status'],
            'title': row['title'],
            'items_count': row['items_count'],
            'date_shamsi': shamsi_date
        })
    return render_template('transfer_list.html', transfers=transfers)

@transfer_bp.route('/add', methods=['GET', 'POST'])
def transfer_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        source_id = int(request.form.get('source_warehouse'))
        dest_id = int(request.form.get('dest_warehouse'))
        final = 1 if request.form.get('final') == 'on' else 0
        description = request.form.get('description', '')
        
        if not (source_id == 1 or dest_id == 1):
            return "خطا: انبار ۱ (نشر اصلی) باید یکی از طرفین جابجایی باشد. <a href='/transfer/add'>بازگشت</a>"
        if source_id == dest_id:
            return "خطا: انبار مبدا و مقصد نمی‌توانند یکسان باشند. <a href='/transfer/add'>بازگشت</a>"
        
        goods_ids = request.form.getlist('goods_id[]')
        numbers = request.form.getlist('number[]')
        prices = request.form.getlist('price[]')
        discounts = request.form.getlist('discount[]')
        
        if not goods_ids:
            return "حداقل یک کالا باید انتخاب شود. <a href='/transfer/add'>بازگشت</a>"
        
        current_timestamp = int(time.time())
        # -1: فروش امانی (خروج از انبار 1) , +1: مرجوعی (ورود به انبار 1)
        status = -1 if source_id == 1 else 1
        
        cursor.execute('''
            INSERT INTO transfer (werehouse, status, date, description)
            VALUES (?, ?, ?, ?)
        ''', (dest_id, status, current_timestamp, description))
        transfer_id = cursor.lastrowid
        
        for i in range(len(goods_ids)):
            goods_id = int(goods_ids[i])
            number = int(numbers[i])
            price = int(prices[i])
            discount_percent = int(discounts[i]) if discounts[i] else 0
            
            cursor.execute('''
                INSERT INTO transfer_details (transfer, goods, number, price, discount)
                VALUES (?, ?, ?, ?, ?)
            ''', (transfer_id, goods_id, number, price, discount_percent))
            
            if final:
                # کاهش از انبار مبدا
                cursor.execute('SELECT id, number FROM stock WHERE goods = ? AND werehouse = ?', (goods_id, source_id))
                source_stock = cursor.fetchone()
                if not source_stock or source_stock['number'] < number:
                    conn.rollback()
                    return f"خطا: موجودی کافی برای کالا {goods_id} در انبار مبدا وجود ندارد. <a href='/transfer/add'>بازگشت</a>"
                new_source = source_stock['number'] - number
                if new_source == 0:
                    cursor.execute('DELETE FROM stock WHERE id = ?', (source_stock['id'],))
                else:
                    cursor.execute('UPDATE stock SET number = ? WHERE id = ?', (new_source, source_stock['id']))
                
                # افزایش به انبار مقصد
                cursor.execute('SELECT id, number FROM stock WHERE goods = ? AND werehouse = ?', (goods_id, dest_id))
                dest_stock = cursor.fetchone()
                if dest_stock:
                    cursor.execute('UPDATE stock SET number = ? WHERE id = ?', (dest_stock['number'] + number, dest_stock['id']))
                else:
                    cursor.execute('INSERT INTO stock (goods, werehouse, number) VALUES (?, ?, ?)', (goods_id, dest_id, number))
                
                if len({source_id, dest_id}.intersection({2,3})) == 1:
                    cursor.execute('SELECT book FROM goods WHERE id = ?', (goods_id,))
                    b = cursor.fetchone()
                    book_id = b['book']
                    if status == 1:
                        cursor.execute('UPDATE goods SET print = print + ? WHERE id = ?', (number, goods_id))
                        cursor.execute('UPDATE book SET print = print + ? WHERE id = ?', (number, book_id))
                    else:
                        cursor.execute('UPDATE goods SET print = print - ? WHERE id = ?', (number, goods_id))
                        cursor.execute('UPDATE book SET print = print - ? WHERE id = ?', (number, book_id))
        
        conn.commit()
        conn.close()
        return f'<h3>جابجایی {"نهایی" if final else "پیش‌فاکتور"} با موفقیت ثبت شد.</h3><a href="/transfer/view">بازگشت به لیست</a>'
    
    else:
        # GET: نمایش فرم
        # انبارها با نام مخاطب
        cursor.execute('''
            SELECT w.id, c.name as contact_name 
            FROM warehouse w
            JOIN contact c ON w.contact = c.id
        ''')
        warehouses = cursor.fetchall()
        # کالاها با نوبت چاپ و قیمت فروش
        cursor.execute('''
            SELECT g.id, b.name as book_name, g.number as print_number, 
                   COALESCE(l.sell, 0) as sell_price
            FROM goods g
            JOIN book b ON g.book = b.id
            LEFT JOIN list l ON l.goods = g.id
            WHERE g.status = 1
            ORDER BY b.name
        ''')
        goods_list = cursor.fetchall()
        conn.close()
        return render_template('transfer_form.html', warehouses=warehouses, goods=goods_list)

@transfer_bp.route('/invoice/<int:transfer_id>')
def transfer_invoice(transfer_id):
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.werehouse as source_warehouse, t.status, t.date, t.description,
               (CASE WHEN t.status = -1 THEN 'فروش امانی' ELSE 'مرجوع از فروش' END) as title
        FROM transfer t
        WHERE t.id = ?
    ''', (transfer_id,))
    transfer = cursor.fetchone()
    if not transfer:
        return "فاکتور یافت نشد.", 404
    
    # اقلام به همراه قطع، جلد، نوبت چاپ
    cursor.execute('''
        SELECT td.id, td.number, td.price, td.discount,
               g.id as goods_id, g.number as print_number, g.cover, g.size,
               b.name as book_name, b.second as book_second
        FROM transfer_details td
        JOIN goods g ON td.goods = g.id
        JOIN book b ON g.book = b.id
        WHERE td.transfer = ?
    ''', (transfer_id,))
    items = cursor.fetchall()
    
    # تعیین طرف دوم (مقصد یا مبدأ غیر از ۱)
    second_party_warehouse_id = transfer['source_warehouse']  # چون انبار دیگر همان طرف دوم است (مبدأ یا مقصد)
    cursor.execute('''
        SELECT c.name, c.code, c.address, c.phone, c.mobile, c.account, c.type
        FROM warehouse w
        JOIN contact c ON w.contact = c.id
        WHERE w.id = ?
    ''', (second_party_warehouse_id,))
    second_party = cursor.fetchone()
    
    conn.close()
    
    # محاسبه مبالغ
    subtotal = 0
    total_item = 0
    for item in items:
        item_total = item['number'] * item['price'] * (1 - item['discount'] / 100)
        subtotal += item_total
        total_item += item['number']
    total = subtotal
    
    date_shamsi = jdatetime.datetime.fromtimestamp(transfer['date']).strftime("%Y/%m/%d")
    print_time = jdatetime.datetime.now().strftime("%H:%M:%S - %Y/%m/%d")

    return render_template('transfer_invoice.html',
                           transfer=transfer,
                           items=items,
                           total=total,
                           date_shamsi=date_shamsi,
                           print_time=print_time,
                           second_party=second_party,
                           total_item=total_item,
                           company=company_info)