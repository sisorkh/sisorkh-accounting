from core.database import db_manager
from flask import render_template, redirect, url_for, Blueprint, request
from libraries import superuser_id
import time
from .sms import send_sms, sms_template
from libraries.tools import format_number

reckoning_bp = Blueprint('reckoning', __name__, url_prefix='/reckoning')

@reckoning_bp.route('/')
def reckoning():
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, balance FROM contact ORDER BY name')
    contacts = cursor.fetchall()
    conn.close()
    return render_template('reckoning.html', contacts=contacts)

@reckoning_bp.route('/settle/<int:contact_id>', methods=['POST'])
def settle_contact(contact_id):
    if contact_id == superuser_id:
        return redirect(url_for('reckoning.reckoning'))
    
    sms_status = request.form.get('sms')
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT balance, mobile FROM contact WHERE id = ?', (contact_id,))
    row = cursor.fetchone()
    if not row:
        return "مخاطب یافت نشد", 404
    balance = row['balance']
    if balance == 0:
        return redirect(url_for('reckoning.reckoning'))
    # ثبت تسویه در financial (مبلغ معکوس)
    settle_amount = -balance
    current_timestamp = int(time.time())
    cursor.execute('INSERT INTO financial (contact, amount, date) VALUES (?, ?, ?)',
                   (contact_id, settle_amount, current_timestamp))
    cursor.execute('UPDATE contact SET balance = 0 WHERE id = ?', (contact_id,))
    cursor.execute('UPDATE contact SET balance = balance + ? WHERE id = ?', (settle_amount, superuser_id))
    conn.commit()
    conn.close()

    if sms_status == "1" and settle_amount < 0: #پرداخت از طرف نشر
        mobile = row['mobile']
        if mobile:
            text = sms_template['payment'].format(format_number(abs(settle_amount)))
            send_sms(mobile, text)
    
    return redirect(url_for('reckoning.reckoning'))