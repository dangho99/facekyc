from datetime import datetime
from .database import connect_db, close_db


def get_timestamp():
    formatter = "%Y-%m-%d %H:%M:%S"
    return datetime.fromtimestamp(time.time()).strftime(formatter)


def save_register_history(user_id, face_images, message, method="add"):
    collection = connect_db("register_history")
    record = {
        "timestamp": get_timestamp(),
        "user_id": user_id,
        "face_images": face_images,
        "message": message,
        "method": method
    }
    collection.insert_one(record)
    close_db()
    return


def save_verify_history(user_id, face_images, gate_location, status, method="add"):
    collection = connect_db("verify_history")
    record = {
        "timestamp": get_timestamp(),
        "user_id": user_id,
        "face_images": face_images,
        "gate_location": gate_location,
        "status": status,
        "method": method
    }
    collection.insert_one(record)
    close_db()
    return