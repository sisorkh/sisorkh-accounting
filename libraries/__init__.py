from libraries import jdatetime
from libraries import tools
from libraries.config import superuser_id
from libraries.config import company_info
start_time = jdatetime.datetime.now()
start_time = f"{start_time.hour:02d}:{start_time.minute:02d}:{start_time.second:02d} {start_time.year:04d}/{start_time.month:02d}/{start_time.day:02d}"