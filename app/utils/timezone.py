from datetime import datetime
import pytz


def get_indonesia_time():
    indonesia_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(indonesia_tz)


def format_indonesia_time(dt):
    if dt is None:
        return None
    
    indonesia_tz = pytz.timezone('Asia/Jakarta')
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    indonesia_dt = dt.astimezone(indonesia_tz)
    return indonesia_dt.strftime('%Y-%m-%d %H:%M:%S')


def get_utc_time():
    return datetime.now(pytz.utc)
