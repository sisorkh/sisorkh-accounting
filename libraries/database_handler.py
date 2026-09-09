import sqlite3
import shutil
import os
import glob
from libraries import jdatetime
from libraries.schema import tables
from libraries.tools import get_file_hash

class DatabaseManager:
    def __init__(self):
        self.db_dir = "database"
        self.main_db_path = os.path.join(self.db_dir, "database.db")
        self.backup_path = os.path.join(self.db_dir, "backup")
        # ایجاد پوشه دیتابیس اگر وجود ندارد
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        self._prepare_database()
        self.create_backup()

    def _prepare_database(self):
        # اگر فایل اصلی وجود ندارد، یک دیتابیس خام بساز
        if not os.path.exists(self.main_db_path):
            self._create_initial_schema(self.main_db_path)

    def _build_create_sql(self, table_name, dtypes):
        dtype_to_sqlite = {
            'int64': 'INTEGER',
            'float64': 'REAL',
            'string': 'TEXT',
            'category': 'TEXT',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP',
        }
        fields = []
        for col, dtype in dtypes.items():
            sql_type = dtype_to_sqlite.get(dtype, 'TEXT')
            if col.upper() == 'ID':
                fields.append(f"{col} INTEGER PRIMARY KEY AUTOINCREMENT")
            else:
                fields.append(f'"{col}" {sql_type}')
        joined_fields = ",\n    ".join(fields)
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {joined_fields}\n);"


    def _create_initial_schema(self, path):
        """ساختار اولیه جداول را اینجا تعریف می‌کنیم"""
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        for table_name, dtypes in tables.items():
            sql = self._build_create_sql(table_name, dtypes)
            cursor.execute(sql)

        father = ''
        year = ''
        code = ''
        booklet = ''
        mobile = ''
        phone = ''
        address = ''
        postal = ''
        account = ''
        email = ''
        balance = 0
        data = [
            {"type":0, "name":"نشر سی‌سرخ"},
            {"type":2, "name":"وب‌سایت"},
            {"type":2, "name":"متفرقه"},
            {"type":2, "name":"ضایعات"},
            {"type":2, "name":"مفقودی"},
            {"type":0, "name":"وزارت ارشاد"}
        ]
        for d in data:
            cursor.execute('''
                INSERT INTO contact (type, name, father, year, code, booklet, mobile, phone, address, postal, account, email, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (d['type'], d['name'], father, year, code, booklet, mobile, phone, address, postal, account, email, balance))
        cursor.execute('INSERT INTO warehouse (contact) VALUES (?)', (1,))
        cursor.execute('INSERT INTO warehouse (contact) VALUES (?)', (3,))
        cursor.execute('INSERT INTO warehouse (contact) VALUES (?)', (4,))
        conn.commit()
        conn.close()

    def get_connection(self):
        """اتصال به دیتابیس کش برای انجام عملیات"""
        conn = sqlite3.connect(self.main_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_backup(self):
        """ایجاد بکاپ از دیتابیس اصلی"""
        # ایجاد پوشه بکاپ اگر وجود ندارد
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
        all_backups = glob.glob(os.path.join(self.backup_path, "*.db"))
        all_backups.sort(key=os.path.getctime)

        change = True
        if len(all_backups):
            main_db_hash = get_file_hash(self.main_db_path)
            last_db_hash = get_file_hash(all_backups[-1])
            if main_db_hash == last_db_hash:
                change = False
                while len(all_backups) > 15:
                    oldest = all_backups.pop(0)
                    os.remove(oldest)
            else:
                while len(all_backups) > 14:
                    oldest = all_backups.pop(0)
                    os.remove(oldest)

        if change:
            # نام فایل بکاپ بر اساس تاریخ و زمان شمسی
            now = jdatetime.datetime.now()
            backup_filename = f"{now.year:04d}.{now.month:02d}.{now.day:02d}.{now.hour:02d}.{now.minute:02d}.{now.second:02d}.db"
            backup_path = os.path.join(self.backup_path, backup_filename)
        
            # کپی فایل اصلی
            shutil.copy2(self.main_db_path, backup_path)
            return backup_filename[:len(backup_filename)-3]