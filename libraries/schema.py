tables = {
    'contact': {
        'id': 'int64', # آی‌دی یکتای اصلی
        'type': 'int64', #حقیقی 0 حقوقی 1 سایر 2
        'name': 'string',
        'father': 'string',
        'year': 'int64', #عدد چهار رقمی
        'code': 'string', # کد ملی
        'booklet': 'string', # شماره شناسنامه
        'mobile': 'string',
        'phone': 'string',
        'address': 'string',
        'postal': 'string', # کد پستی
        'account': 'string', # شماره حساب بانکی
        'email': 'string',
        'balance':'int64', #تراز مالی
    },
    'book': {
        'id': 'int64',
        'name': 'string',
        'second':'string',
        'year': 'int64', #سال معرفی
        'print': 'int64',
        'electronic': 'int64',
        'audio': 'int64',
        'pod': 'int64',
        'share_type': 'int64', # درصد از سود 0 درصد از پشت جلد 1 یکجا 2
    },
    'cost':{
        'id':'int64',
        'book':'int64',
        'description':'string',
        'amount':'int64',
        'date':'int64',
    },
    'list':{
        'id':'int64',
        'goods':'int64',
        'buy':'int64',
        'sell':'int64',
        'date':'int64',
        'sku':'int64',
    },
    'share': {
        'id': 'int64',
        'book': 'int64',
        'contact': 'int64',
        'share': 'float64',
    },
    'warehouse':{
        'id': 'int64',
        'contact': 'int64',
    },
    'goods': {
        'id': 'int64',
        'book': 'int64',
        'isbn':'int64',
        'cover': 'int64', # شومیز 0 گالینگور 1 شومیز قابردار 2 گالینگور قابدار 3
        'size': 'int64', # رقعی 0 جیبی 1 پالتویی 2 وزیری 3 رحلی 4 نقلی 5 خشتی 6
        'page': 'int64', # صفحه
        'weight': 'int64', # وزن
        'sold':'int64',
        'print':'int64', # مجموع تیراژ همه‌ی نوبت‌های چاپ (از جدول prints)
    },
    'prints': {
        'id': 'int64',
        'goods': 'int64',
        'number': 'int64', # نوبت چاپ
        'tirage': 'int64', # تیراژ همین نوبت
        'year': 'int64', # سال چاپ همین نوبت
    },
    'stock': {
        'id': 'int64',
        'goods':'int64',
        'werehouse':'int64',
        'number':'int64',
    },
    'transfer': {
        'id': 'int64',
        'werehouse':'int64',
        'status':'int64', # خروج یا فروش امانی -1 ورود یا مرجوعی +1
        'date':'int64',
        'description':'string'
    },
    'transfer_details': {
        'id': 'int64',
        'transfer': 'int64',
        'goods': 'int64',
        'number': 'int64',
        'price': 'int64',
        'discount': 'float64',
    },
    'sales': {
        'id': 'int64',
        'contact': 'int64',
        'werehouse':'int64',
        'description':'string', # توضیحات اختیاری
        'date': 'int64',
        'shipping_method': 'int64',# حضوری 0 پست 1 باربری پخش 2 پیک 3 سایر 4
        'shipping_cost': 'int64',
        'final': 'int64' #پیش‌فاکتور 0 و نهایی 1
    },
    'sales_details':{
        'id':'int64',
        'goods':'int64',
        'sales':'int64',
        'number': 'int64', # تعداد
        'price': 'int64', # قیمت
        'discount': 'int64', #تخفیف
        'type': 'int64', # چاپی 0 الکترونیکی 1 صوتی 2
    },
    'purchase': {
        'id': 'int64',
        'contact': 'int64',
        'werehouse':'int64',
        'description':'string', # توضیحات اختیاری
        'date': 'int64',
        'shipping_method': 'int64',# حضوری 0 پست 1 باربری پخش 2 پیک 3 سایر 4
        'shipping_cost': 'int64',
        'final': 'int64' #پیش‌فاکتور 0 و نهایی 1
    },
    'purchase_details':{
        'id':'int64',
        'goods':'int64',
        'purchase':'int64',
        'number': 'int64', # تعداد
        'price': 'int64', # قیمت
        'discount': 'int64', #تخفیف
    },
    'financial':{
        'id':'int64',
        'contact': 'int64',
        'amount':'int64',
        'date': 'int64',
        'description':'string',
    },
    'report':{
        'id':'int64',
        'amount':'int64',
        'balance':'int64',
        'warehouse_1':'int64', # انبار نشر
        'warehouse_2':'int64', # انبار ضایعات
        'warehouse_3':'int64', # انبار مفقودی
        'warehouse_4':'int64', # انبارهای امانی
        'date': 'int64',
    }
}