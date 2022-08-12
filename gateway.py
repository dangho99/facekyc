from gateway import face_detection

app = face_detection()


@app.before_request
def before_request():
    pass


@app.after_request
def after_request(response):
    from flask import request

    return response


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8501", debug=True)
