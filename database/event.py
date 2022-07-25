from . import db


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_hash = db.Column(db.String(200))
    event_type = db.Column(db.String(20))
    event_time = db.Column(db.Integer())
    predicted = db.Column(db.String(20))
    actual = db.Column(db.String(20))
    score = db.Column(db.Float())
    message_code = db.Column(db.Integer())
    is_success = db.Column(db.Boolean())
