from core.database import db_manager
from flask import Blueprint

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/')
def backup():
    try:
        backup_file = db_manager.create_backup()
        if backup_file:
            return f'<h3>✅ بکاپ با موفقیت ایجاد شد: {backup_file}</h3><a href="/">بازگشت به صفحه اصلی</a>'
        else:
            return f'<h3>به علت تکراری بودن بک‌‌آپ گرفته نشد</h3><a href="/">بازگشت به صفحه اصلی</a>'
    except Exception as e:
        return f'<h3>❌ خطا در ایجاد بکاپ: {str(e)}</h3><a href="/">بازگشت</a>'