from flask import Flask
from .index import index_bp
from .backup import backup_bp
from .contact import contact_bp
from .warehouse import warehouse_bp
from .book import book_bp
from .goods import goods_bp
from .financial import financial_bp
from .cost import cost_bp
from .purchase import purchase_bp
from .transfer import transfer_bp
from .list import list_bp
from .sales import sales_bp
from .reckoning import reckoning_bp
from libraries.tools import (
    format_number,
    persian_numbers,
    format_discount
)

app = Flask("__main__")
app.jinja_env.filters['persian'] = persian_numbers
app.jinja_env.filters['format_number'] = format_number
app.jinja_env.filters['format_discount'] = format_discount

app.register_blueprint(index_bp) #خانه
app.register_blueprint(backup_bp) #بک‌آپ
app.register_blueprint(contact_bp) #مخاطب
app.register_blueprint(warehouse_bp) #انبار
app.register_blueprint(book_bp) #کتاب
app.register_blueprint(goods_bp) #کالا
app.register_blueprint(financial_bp) #مالی   
app.register_blueprint(cost_bp) #هزینه
app.register_blueprint(purchase_bp) #خرید
app.register_blueprint(transfer_bp) #جابه‌جایی   
app.register_blueprint(list_bp) #لیست قیمت
app.register_blueprint(sales_bp) #فروش
app.register_blueprint(reckoning_bp) #تسویه‌حساب