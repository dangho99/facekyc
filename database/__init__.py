from flask_sqlalchemy import SQLAlchemy
import os


db = SQLAlchemy()
DB_PATH = os.path.join(os.getcwd(), "database", 'app.db')


def create_database(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    db.init_app(app)

    from database.user import User
    from database.event import Event

    if not os.path.exists(DB_PATH):
        db.create_all(app=app)
        print('Created Database! on {}'.format(DB_PATH))

