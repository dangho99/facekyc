import os
from flask import Flask
from flask_socketio import SocketIO
from .user import user
from .feedback import feedback
from .monitor import monitor
from keeper.environments import SystemEnv


socket_io = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    app.register_blueprint(user, url_prefix='/api/user')
    app.register_blueprint(feedback, url_prefix='/api/feedback')
    app.register_blueprint(monitor, url_prefix='/api/monitor')

    socket_io.init_app(app)

    return app



