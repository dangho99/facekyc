from datetime import datetime
from .database import connect_db, close_db
import time


def get_timestamp():
    formatter = "%Y-%m-%d %H:%M:%S"
    return datetime.fromtimestamp(time.time()).strftime(formatter)


def save_logs(data, collection_name):
    collection = connect_db(collection_name)
    collection.insert_one(data)
    close_db()
    return
