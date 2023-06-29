from datetime import datetime
import hashlib
import time


def md5(s: str):
    s = hashlib.md5(s.encode()).hexdigest()
    return s


def get_datetime(timestamp=None):
    formatter = "%Y-%m-%dT%H:%M:%S"
    if timestamp is None:
        timestamp = get_timestamp()
    return datetime.fromtimestamp(timestamp).strftime(formatter)


def get_timestamp():
    return int(time.time())
