from core.database import db_manager
from core.secret import secret
from flask import render_template, request, Response, stream_with_context, Blueprint
import time
from libraries import jdatetime
import requests
from requests.auth import HTTPBasicAuth
import json
import sys

list_bp = Blueprint('list', __name__, url_prefix='/list')

@list_bp.route('/', methods=['GET', 'POST'])
def price_list():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        def generate():
            goods_ids = request.form.getlist('goods_id')
            buy_prices = request.form.getlist('buy_price')
            sell_prices = request.form.getlist('sell_price')
            skus = request.form.getlist('sku')
            
            current_timestamp = int(time.time())
            
            # دریافت اطلاعات قبلی (نام کتاب، sell، sku)
            placeholders = ','.join('?' * len(goods_ids))
            cursor.execute(f'''
                SELECT g.id, b.name as book_name, l.sell, l.buy, l.sku
                FROM goods g
                JOIN book b ON g.book = b.id
                JOIN list l ON l.goods = g.id
                WHERE g.id IN ({placeholders})
            ''', goods_ids)
            old_info = {row['id']: {
                'name': row['book_name'],
                'sell': row['sell'],
                'buy': row['buy'],
                'sku': row['sku'],
            } for row in cursor.fetchall()}
            
            yield """<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>گزارش لحظه‌ای به‌روزرسانی قیمت‌ها</title>
    <style>
        body { font-family: Tahoma, sans-serif; margin: 20px; }
        ul { list-style: none; padding: 0; }
        li { margin: 8px 0; padding: 5px; border-radius: 5px; background: #f4f4f4; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        .info { color: blue; }
    </style>
</head>
<body>
<h2>در حال پردازش تغییرات...</h2>
<ul id="log">"""
            
            connection = False
            for i in range(len(goods_ids)):
                goods_id = int(goods_ids[i])
                new_buy = int(buy_prices[i]) if buy_prices[i] else 0
                new_sell = int(sell_prices[i]) if sell_prices[i] else 0
                new_sku = int(skus[i]) if skus[i] else 0
                force = 1 if request.form.get(f'force_{goods_id}') == 'on' else 0
                
                old = old_info.get(goods_id, {})
                old_sell = old.get('sell', 0)
                old_buy = old.get('buy', 0)
                old_sku = old.get('sku', 0)
                book_name = old.get('name', 'نامشخص')
                
                # به‌روزرسانی دیتابیس فقط در صورت تغییر هر یک از فیلدها
                cursor.execute('''
                    UPDATE list 
                    SET buy = ?, sell = ?, sku = ?, date = ?
                    WHERE goods = ? AND (buy != ? OR sell != ? OR sku != ?)
                ''', (new_buy, new_sell, new_sku, current_timestamp,
                      goods_id, new_buy, new_sell, new_sku))
                
                if cursor.rowcount == 0 and not force:
                    continue
                
                # ساخت پیام تغییرات
                changes = []
                if new_sell != old_sell:
                    changes.append(f"sell: {old_sell} → {new_sell}")
                if new_buy != old_buy:
                    changes.append(f"buy: {old_buy} → {new_buy}")
                if new_sku != old_sku:
                    changes.append(f"sku: {old_sku} → {new_sku}")
                
                if not changes and not force:
                    continue
                
                msg = f"📚 {book_name} (کد {goods_id}): " + " | ".join(changes)
                cls = "info"
                
                # اگر قیمت فروش تغییر کرده، به API ارسال کن
                if new_sell != old_sell or force:
                    if new_sku:
                        try:
                            if not connection:
                                site_url = 'https://www.sisorkh.com'
                                consumer_key = secret['consumer_key']
                                consumer_secret = secret['consumer_secret']
                                api_secret = secret['api_secret']
                                session = requests.Session()
                                session.auth = HTTPBasicAuth(consumer_key, consumer_secret)
                                session.headers.update({'X-API-Secret': api_secret})
                                connection = True
                        except:
                            msg += f" | ❌ خطا در ساخت نشست با وب‌سایت هدف"
                        try:
                            if connection:
                                search_params = {'sku': new_sku}
                                resp = session.get(f"{site_url}/wp-json/wc/v3/products", params=search_params)
                                if resp.status_code != 200:
                                    msg += "خطا در پیدا کردن sku"
                                    continue
                                products = resp.json()
                                if not products:
                                    msg += "sku پیدا نشد"
                                    continue
                                product = products[0]
                                product_id = product['id']
                                update_data = {'regular_price': str(new_sell)}
                                resp = session.put(f"{site_url}/wp-json/wc/v3/products/{product_id}",json=update_data)
                                if resp.status_code == 200:
                                    msg += f" | ✅ وب‌سایت به‌روز شد"
                                else:
                                    msg += f" | ❌ خطای شماره‌ی {resp.status_code}"
                        except:
                            msg += f" | ❌ خطای ناشناخته در آپدیت وب‌سایت"
                        time.sleep(1.5)
                    else:
                        msg += f" | مقادیر sku و id جهت به‌روزرسانی اجباری است"
                yield f'<li class="{cls}">{msg}</li>'
                sys.stdout.flush()
            if connection:
                try:
                    session.close()
                except:
                    pass
            conn.commit()
            conn.close()
            
            yield """</ul>
<a href="/list">🔙 بازگشت به لیست قیمت</a>
<script>
    const logDiv = document.getElementById('log');
    const observer = new MutationObserver(() => {
        logDiv.lastElementChild?.scrollIntoView({ behavior: 'smooth' });
    });
    observer.observe(logDiv, { childList: true });
</script>
</body>
</html>"""
        
        return Response(stream_with_context(generate()), mimetype='text/html')
    
    else:
        # GET: نمایش لیست قیمت‌ها با فیلدهای جدید
        cursor.execute('''
            SELECT l.id, l.goods, l.buy, l.sell, l.date, l.sku,
                   g.id as goods_id, g.isbn, g.cover, g.size,
                   b.name as book_name, b.second as book_second
            FROM list l
            JOIN goods g ON l.goods = g.id
            JOIN book b ON g.book = b.id
            ORDER BY b.name
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for row in rows:
            shamsi_date = jdatetime.datetime.fromtimestamp(row['date']).strftime("%Y/%m/%d") if row['date'] else ''
            items.append({
                'id': row['id'],
                'goods_id': row['goods'],
                'book_name': f"{row['book_name']} {row['book_second'] or ''}".strip(),
                'isbn': row['isbn'],
                'size': row['size'],
                'cover': row['cover'],
                'buy': row['buy'],
                'sell': row['sell'],
                'sku': row['sku'] or 0,
                'date_shamsi': shamsi_date
            })
        return render_template('price_list.html', items=items)