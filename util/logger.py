from datetime import datetime
import time


def get_timestamp():
    formatter = "%Y-%m-%d %H:%M:%S"
    return datetime.fromtimestamp(time.time()).strftime(formatter)
