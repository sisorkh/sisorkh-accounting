from core.database import db_manager
from flask import render_template, request, Blueprint
import time
from libraries import jdatetime, superuser_id, company_info
from libraries.tools import shamsi_to_timestamp

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/view')
def sales_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    #برای فیلتر تاریخ
    start_year = request.args.get('start_year', '')
    start_month = request.args.get('start_month', '')
    start_day = request.args.get('start_day', '')
    end_year = request.args.get('end_year', '')
    end_month = request.args.get('end_month', '')
    end_day = request.args.get('end_day', '')
    #برای فیلتر انبار
    warehouse_id = request.args.get('warehouse_id', '')

    cursor.execute('''
        SELECT w.id, c.name as contact_name
        FROM warehouse w
        JOIN contact c ON w.contact = c.id
        WHERE w.id != 0
        ORDER BY c.name
    ''')
    warehouses = cursor.fetchall()

    start_timestamp = None
    if start_year and start_month and start_day:
        start_date_str = f"{start_year}-{start_month.zfill(2)}-{start_day.zfill(2)}"
        start_timestamp = shamsi_to_timestamp(start_date_str)  # همان تابع قبلی که جداکننده - را می‌پذیرد
    
    end_timestamp = None
    if end_year and end_month and end_day:
        end_date_str = f"{end_year}-{end_month.zfill(2)}-{end_day.zfill(2)}"
        end_timestamp = shamsi_to_timestamp(end_date_str)
        if end_timestamp:
            end_timestamp += 86399

    query = '''
        SELECT i.id, i.contact, c.name as contact_name, i.werehouse, i.description, 
               i.date, i.shipping_method, i.shipping_cost, i.final,
               (SELECT COUNT(*) FROM sales_details WHERE sales=i.id) as items_count
        FROM sales i
        JOIN contact c ON i.contact = c.id
        WHERE 1=1
    '''
    params = []
    if start_timestamp:
        query += " AND i.date >= ?"
        params.append(start_timestamp)
    if end_timestamp:
        query += " AND i.date <= ?"
        params.append(end_timestamp)
    if warehouse_id:
        query += " AND i.werehouse = ?"
        params.append(warehouse_id) 
    
    query += " ORDER BY i.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    sales = []
    for row in rows:
        shamsi_date = jdatetime.datetime.fromtimestamp(row['date']).strftime("%Y/%m/%d")
        sales.append({
            'id': row['id'],
            'contact_name': row['contact_name'],
            'werehouse': row['werehouse'],
            'date_shamsi': shamsi_date,
            'final': row['final'],
            'items_count': row['items_count']
        })
    return render_template('sales_list.html', sales=sales,
                           start_year=start_year, start_month=start_month, start_day=start_day,
                           end_year=end_year, end_month=end_month, end_day=end_day,
                           warehouses=warehouses, selected_warehouse=warehouse_id)

@sales_bp.route('/add', methods=['GET', 'POST'])
def sales_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        contact_id = request.form.get('contact')
        warehouse_id = int(request.form.get('warehouse'))
        description = request.form.get('description', '')
        shipping_method = request.form.get('shipping_method')
        shipping_cost = int(request.form.get('shipping_cost') or 0)
        final = 1 if request.form.get('final') == 'on' else 0
        register_payment = 1 if request.form.get('register_payment') == 'on' else 0
        contribution = 1 if request.form.get('contribution') == 'on' else 0
        
        if not contact_id:
            return "مخاطب الزامی است. <a href='/sales/add'>بازگشت</a>"
        
        goods_ids = request.form.getlist('goods_id[]')
        numbers = request.form.getlist('number[]')
        prices = request.form.getlist('price[]')
        discounts = request.form.getlist('discount[]')
        # types از فرم می‌آید (0 چاپی، 1 الکترونیک، 2 صوتی)
        types = request.form.getlist('type[]')
        
        if not goods_ids:
            return "حداقل یک کالا باید انتخاب شود. <a href='/sales/add'>بازگشت</a>"
        
        current_timestamp = int(time.time())
        
        # درج فاکتور فروش
        cursor.execute('''
            INSERT INTO sales (contact, werehouse, description, date, shipping_method, shipping_cost, final)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (contact_id, warehouse_id, description, current_timestamp, shipping_method, shipping_cost, final))
        sales_id = cursor.lastrowid
        
        total = 0
        items_data = []
        for i in range(len(goods_ids)):
            gid = int(goods_ids[i])          # برای مجازی منفی است
            number = int(numbers[i])
            price = int(prices[i])
            discount_percent = int(discounts[i]) if discounts[i] else 0
            type_id = int(types[i]) if types[i] else 0
            cursor.execute('SELECT COALESCE(buy, 0) FROM list WHERE goods = ?', (gid,))
            buy_price = cursor.fetchone()[0]

            row_total = int(number * price * (1 - discount_percent / 100))
            total += row_total

            items_data.append({
                'goods': gid,
                'number': number,
                'type': type_id,
                'price': price,
                'discount': discount_percent,
                'buy_price': buy_price
            })
            
            cursor.execute('''
                INSERT INTO sales_details (sales, goods, number, price, discount, type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sales_id, gid, number, price, discount_percent, type_id))
        
        #total += shipping_cost
        
        if final:
            # 1. به‌روزرسانی stock و sold فقط برای کالاهای فیزیکی
            if warehouse_id != 0:
                cursor.execute('SELECT goods, number, type FROM sales_details WHERE sales = ?', (sales_id,))
                for row in items_data:
                    if row['goods'] > 0 and row['type'] == 0:
                        gid = row['goods']
                        num = row['number']
                        cursor.execute('UPDATE goods SET sold = sold + ? WHERE id = ?', (num, gid))
                        cursor.execute('SELECT id, number FROM stock WHERE goods = ? AND werehouse = ?', (gid, warehouse_id))
                        st = cursor.fetchone()
                        if st:
                            new_num = st['number'] - num
                            if new_num == 0:
                                cursor.execute('DELETE FROM stock WHERE id = ?', (st['id'],))
                            else:
                                cursor.execute('UPDATE stock SET number = ? WHERE id = ?', (new_num, st['id']))
                        else:
                            conn.rollback()
                            return f"خطا: کالا {gid} در انبار موجود نیست."

            # 2. به‌روزرسانی آمار فروش در جدول book (برای همه فاکتورهای نهایی، حتی اهدایی)
            cursor.execute('''
                SELECT d.goods, d.number, d.type
                FROM sales_details d
                WHERE d.sales = ?
            ''', (sales_id,))
            for row in items_data:
                gid = row['goods']
                num = row['number']
                typ = row['type']
                if typ == 0:   # چاپی
                    cursor.execute('SELECT book FROM goods WHERE id = ?', (gid,))
                    b = cursor.fetchone()
                    book_id = b['book']
                    cursor.execute('UPDATE book SET print = print + ? WHERE id = ?', (num, book_id))
                elif typ == 1:   # الکترونیک
                    book_id = abs(gid)
                    cursor.execute('UPDATE book SET electronic = electronic + ? WHERE id = ?', (num, book_id))
                elif typ == 2:   # صوتی
                    book_id = abs(gid)
                    cursor.execute('UPDATE book SET audio = audio + ? WHERE id = ?', (num, book_id))
                elif typ == 3:   # POD
                    book_id = abs(gid)
                    cursor.execute('UPDATE book SET pod = pod + ? WHERE id = ?', (num, book_id))

            # 3. محاسبه سود و توزیع (فقط در صورت عدم تیک contribution)
            if not contribution:
                
                for row in items_data:
                    # پیدا کردن book_id برای توزیع سهام
                    if gid > 0:
                        cursor.execute('SELECT book FROM goods WHERE id = ?', (gid,))
                        row_book = cursor.fetchone()
                        book_id = row_book['book'] if row_book else None
                    else:
                        book_id = abs(gid)   # برای کالای مجازی، book_id = -gid
                    
                    cursor.execute('SELECT share_type FROM book WHERE id = ?', (book_id,))
                    row_book = cursor.fetchone()
                    share_type = row_book['share_type']
                    if share_type == 2:
                        continue

                    gid = row['goods']
                    num = row['number']
                    sell = row['price']
                    typ = row['type']
                    disc = row['discount']

                    # سود خالص
                    if share_type == 0:
                        buy = row['buy_price']
                        final_price = sell * (1 - disc / 100.0)
                        # محاسبه سود هر واحد
                        if warehouse_id == 0 or gid < 0:   # مجازی (انبار مجازی یا کد منفی)
                            profit_per_unit = final_price   # هزینه خرید صفر
                        else:
                            profit_per_unit = final_price - buy
                        total_profit = profit_per_unit * num
                    
                    # درصد پشت جلد
                    elif share_type == 1:
                        total_profit = sell * num
                        if disc == 100:
                            continue

                    if total_profit and book_id:
                        cursor.execute('SELECT contact, share FROM share WHERE book = ?', (book_id,))
                        shares = cursor.fetchall()
                        for sh in shares:
                            share_amount = int(total_profit * (sh['share'] / 100.0))
                            cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (share_amount, sh['contact']))

                # ثبت مالی و تراز مشتری (فقط در صورت عدم contribution)
                if total:
                    if register_payment:
                        cursor.execute('INSERT INTO financial (contact, amount, date) VALUES (?, ?, ?)', (contact_id, total, current_timestamp))
                        cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (total, superuser_id))
                    else:
                        cursor.execute('UPDATE contact SET balance = balance - ? WHERE id = ?', (total, contact_id))

            # بیرون از شرط contribution
            conn.commit()
            conn.close()
            return f'<h3>فاکتور فروش {"نهایی" if final else "پیش‌فاکتور"} با موفقیت ثبت شد.</h3><a href="/sales/view">بازگشت به لیست فروش‌ها</a>'
    
    else:
        # GET (فرم)
        cursor.execute('SELECT id, name FROM contact ORDER BY name')
        contacts = cursor.fetchall()
        cursor.execute('''
            SELECT w.id, c.name as contact_name
            FROM warehouse w
            JOIN contact c ON w.contact = c.id
            WHERE w.id != 0
        ''')
        warehouses = cursor.fetchall()
        cursor.execute('''
            SELECT g.id, b.name as book_name, g.number as print_number,
                COALESCE(l.sell, 0) as sell_price, 0 as type
            FROM goods g
            JOIN book b ON g.book = b.id
            LEFT JOIN list l ON l.goods = g.id
            WHERE g.status = 1
            ORDER BY b.name
        ''')
        physical_goods = cursor.fetchall()
        cursor.execute('SELECT id, name as book_name FROM book ORDER BY name')
        books = cursor.fetchall()
        buy_prices = {}
        cursor.execute('''
            SELECT goods, buy FROM list
        ''')
        for row in cursor.fetchall():
            buy_prices[str(row['goods'])] = row['buy']
        virtual_goods = []
        for book in books:
            virtual_goods.append({'id': -book['id'], 'book_name': f"{book['book_name']} (الکترونیک)", 'sell_price': 0, 'type': 1})
            virtual_goods.append({'id': -book['id'], 'book_name': f"{book['book_name']} (صوتی)", 'sell_price': 0, 'type': 2})
            virtual_goods.append({'id': -book['id'], 'book_name': f"{book['book_name']} (POD)", 'sell_price': 0, 'type': 3})
        
        inventory_data = {}
        for w in warehouses:
            cursor.execute('SELECT goods, number FROM stock WHERE werehouse = ?', (w['id'],))
            inv = {str(row['goods']): row['number'] for row in cursor.fetchall()}
            inventory_data[w['id']] = inv
        conn.close()
        return render_template('sales_form.html', contacts=contacts, warehouses=warehouses,
                            physical_goods=physical_goods, virtual_goods=virtual_goods,
                            inventory_data=inventory_data, buy_prices=buy_prices)

@sales_bp.route('/invoice/<int:invoice_id>')
def sales_invoice(invoice_id):
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.id, i.contact, i.werehouse, i.description, i.date, 
               i.shipping_method, i.shipping_cost, i.final,
               c.name as contact_name, c.type as contact_type, c.code as contact_code,
               c.address as contact_address, c.phone as contact_phone, c.mobile as contact_mobile
        FROM sales i
        JOIN contact c ON i.contact = c.id
        WHERE i.id = ?
    ''', (invoice_id,))
    invoice = cursor.fetchone()
    if not invoice:
        return "فاکتور یافت نشد.", 404
    
    cursor.execute('''
        SELECT d.id, d.number, d.price, d.discount, d.type,
               g.id as goods_id, g.number as print_number, g.cover, g.size,
               b.name as book_name, b.second as book_second
        FROM sales_details d
        LEFT JOIN goods g ON d.goods = g.id
        LEFT JOIN book b ON g.book = b.id
        WHERE d.sales = ?
    ''', (invoice_id,))
    items = cursor.fetchall()
    conn.close()
    total_item = 0
    subtotal = 0
    for item in items:
        row_total = item['number'] * item['price'] * (1 - item['discount'] / 100)
        subtotal += row_total
        total_item += item['number']
    total = subtotal + invoice['shipping_cost']
    
    date_shamsi = jdatetime.datetime.fromtimestamp(invoice['date']).strftime("%Y/%m/%d")
    print_time = jdatetime.datetime.now().strftime("%H:%M:%S - %Y/%m/%d")
    
    return render_template('sales_invoice.html',
                           invoice=invoice,
                           items=items,
                           total=total,
                           date_shamsi=date_shamsi,
                           print_time=print_time,
                           total_item=total_item,
                           company=company_info)