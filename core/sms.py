import requests
from core.secret import secret

url = 'https://rest.payamak-panel.com/api/SendSMS/SendSMS'

def send_sms(send_to:str, send_text:str, send_from:str="XXXXXXXX") -> int:
    payload = {
        'username': secret['sms_username]',
        'password': secret['sms_password]',
        'to': send_to,
        'from': send_from,
        'text': send_text
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.status_code
    except:
        return 0
    
sms_template = {
    'payment': 'مبلغ {} تومان از طرف نشر سی‌سرخ به حساب شما واریز خواهد شد.'
}