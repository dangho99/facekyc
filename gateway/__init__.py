import os
from flask import Flask
from flask_socketio import SocketIO
from .face import face

socket_io = SocketIO()


def face_detection():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    app.register_blueprint(face, url_prefix='/api/user')

    socket_io.init_app(app)

    return app



