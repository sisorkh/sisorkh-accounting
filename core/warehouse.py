from core.database import db_manager
from flask import render_template, request, Blueprint

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/warehouse')

@warehouse_bp.route('/view')
def warehouse_view():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    # نمایش انبارها همراه با نام مخاطب
    cursor.execute('''
        SELECT warehouse.id, warehouse.contact, contact.name as contact_name
        FROM warehouse
        JOIN contact ON warehouse.contact = contact.id
    ''')
    warehouses = cursor.fetchall()
    conn.close()
    return render_template('warehouse_list.html', warehouses=warehouses)

@warehouse_bp.route('/add', methods=['GET', 'POST'])
def warehouse_add():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        contact_id = request.form.get('contact')
        # بررسی اینکه آیا این مخاطب قبلاً انبار دارد یا نه (امنیت مضاعف)
        cursor.execute('SELECT id FROM warehouse WHERE contact = ?', (contact_id,))
        if cursor.fetchone():
            conn.close()
            return "خطا: این مخاطب قبلاً دارای انبار است. <a href='/warehouse/add'>بازگشت</a>"
        
        cursor.execute('INSERT INTO warehouse (contact) VALUES (?)', (contact_id,))
        conn.commit()
        conn.close()
        return '<h3>انبار با موفقیت اضافه شد.</h3><a href="/warehouse/view">بازگشت به لیست انبارها</a>'
    
    else:
        # فقط مخاطبانی را نشان بده که هنوز انبار ندارند
        cursor.execute('''
            SELECT id, name FROM contact 
            WHERE id NOT IN (SELECT contact FROM warehouse WHERE contact IS NOT NULL)
        ''')
        contacts_without_warehouse = cursor.fetchall()
        conn.close()
        return render_template('warehouse_form.html', contacts=contacts_without_warehouse)