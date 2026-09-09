from flask import render_template, request, Blueprint
from libraries.tools import english_numbers
from core.database import db_manager

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/view')
def contact_view():
    # فعلاً یک صفحه موقتی برای مشاهده مخاطبان
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contact")
    contacts = cursor.fetchall()
    conn.close()
    return render_template('contact_list.html', contacts=contacts)

@contact_bp.route('/add', methods=['POST'])
def contact_add_post():
    # دریافت داده‌های فرم
    contact_id = request.form.get('id')
    contact_type = request.form.get('type')
    name = request.form.get('name').strip()
    father = request.form.get('father').strip()
    year = english_numbers(request.form.get('year').strip())
    code = english_numbers(request.form.get('code').strip())
    booklet = english_numbers(request.form.get('booklet').strip())
    mobile = english_numbers(request.form.get('mobile').strip())
    phone = english_numbers(request.form.get('phone').strip())
    address = request.form.get('address').strip()
    postal = english_numbers(request.form.get('postal').strip())
    account = english_numbers(request.form.get('account').strip())
    email = english_numbers(request.form.get('email').strip())
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if contact_id:  # ویرایش
        cursor.execute("SELECT balance FROM contact WHERE id=?", (contact_id,))
        current_balance = cursor.fetchone()
        if current_balance:
            balance = current_balance['balance']
        else:
            balance = 0

        cursor.execute('''
            UPDATE contact SET
                type=?, name=?, father=?, year=?, code=?, booklet=?, mobile=?, phone=?,
                address=?, postal=?, account=?, email=?, balance=?
            WHERE id=?
        ''', (contact_type, name, father, year, code, booklet, mobile, phone,
              address, postal, account, email, balance, contact_id))
    else:  # افزودن جدید
        balance = 0
        cursor.execute('''
            INSERT INTO contact (type, name, father, year, code, booklet, mobile, phone, address, postal, account, email, balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (contact_type, name, father, year, code, booklet, mobile, phone, address, postal, account, email, balance))
    
    conn.commit()
    conn.close()
    
    return "<h3>مخاطب با موفقیت ذخیره شد.</h3><a href='/contact/view'>بازگشت به لیست مخاطبان</a>"

@contact_bp.route('/add', methods=['GET'])
def contact_add_form():
    return render_template('contact_form.html', contact=None)

@contact_bp.route('/edit/<int:id>', methods=['GET'])
def contact_edit_form(id):
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contact WHERE id=?", (id,))
    contact = cursor.fetchone()
    conn.close()
    if not contact:
        return "مخاطب یافت نشد", 404
    return render_template('contact_form.html', contact=contact)