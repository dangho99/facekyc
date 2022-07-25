from routes import create_app
from database import create_database

app = create_app()
create_database(app)


@app.before_request
def before_request():
    pass


@app.after_request
def after_request(response):
    from flask import request

    return response


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="9002", debug=True)
