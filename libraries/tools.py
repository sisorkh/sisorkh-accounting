import hashlib
import os
from libraries import jdatetime
from datetime import datetime

def persian_numbers(s):
    if s is None:
        return ''
    persian_map = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return str(s).translate(persian_map)

def english_numbers(s):
    if s is None:
        return ''
    english_map = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    return str(s).translate(english_map)

def format_number(value):
    """تبدیل عدد به فرمت هزارگان (مثل 1,000,000) و سپس به فارسی"""
    if value is None:
        return '۰'
    try:
        # فرمت با کاما
        formatted = f"{int(value):,}"
    except (ValueError, TypeError):
        formatted = str(value)
    # تبدیل ارقام به فارسی
    persian_map = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return formatted.translate(persian_map)

def format_discount(value):
    """تبدیل تخفیف: اگر اعشار صفر بود بدون اعشار نشان بده"""
    if value is None:
        return ''
    try:
        num = float(value)
        if num.is_integer():
            return persian_numbers(int(num))
        else:
            # با یک رقم اعشار (مثلاً 12.5)
            return persian_numbers(f"{num:.1f}")
    except (ValueError, TypeError):
        return persian_numbers(str(value))

def get_file_hash(file_path):
    """محاسبه هش SHA-256 برای یک فایل"""
    if not os.path.exists(file_path):
        return None
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # فایل را تکه تکه می‌خوانیم تا اگر حجیم بود رم پر نشود
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def shamsi_to_timestamp(shamsi_date):
    """تبدیل تاریخ شمسی (فرمت ۱۴۰۳/۰۱/۰۱) به Unix Timestamp"""
    try:
        year, month, day = map(int, shamsi_date.split('-'))
        g_date = jdatetime.date(year, month, day).togregorian()
        return int(datetime(g_date.year, g_date.month, g_date.day).timestamp())
    except:
        return None
    
def apply_date_filter(query, params, start_date, end_date):
    """شرط‌های تاریخ را به کوئری اضافه می‌کند"""
    if start_date:
        ts = shamsi_to_timestamp(start_date)
        if ts:
            query += " AND date >= ?"
            params.append(ts)
    if end_date:
        ts = shamsi_to_timestamp(end_date)
        if ts:
            query += " AND date <= ?"
            params.append(ts + 86399)
    return query, params