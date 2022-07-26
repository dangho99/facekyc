from flask import Flask, request, redirect, url_for, render_template, make_response, jsonify
import os
import json
import glob
from util import dataio
import requests

app = Flask(__name__)


@app.route("/sign-up")
def sign_up():
    return render_template("sign_up.html")


@app.route("/upload-sign-up", methods=["POST"])
def upload_sign_up():
    """Handle the upload of a file."""
    form = request.form

    print("=== Form Data ===")
    upload_key = form.get("userid")

    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Target folder for these uploads.
    target = "uploadr/static/uploads/{}".format(upload_key)
    try:
        os.mkdir(target)
    except:
        if is_ajax:
            return ajax_response(False, "Couldn't create upload directory: {}".format(target))
        else:
            return "Couldn't create upload directory: {}".format(target)

    meta_data = {k: v for k, v in form.items() if k != '__ajax'}
    with open("/".join([target, "metadata.txt"]), "w") as f:
        f.write(json.dumps(meta_data))

    for upload in request.files.getlist("file"):
        filename = upload.filename.rsplit("/")[0]
        destination = "/".join([target, filename])
        print("Accept incoming file:", filename)
        print("Save it to:", destination)
        upload.save(destination)

    if is_ajax:
        return ajax_response(True, upload_key)
    else:
        return redirect(url_for("upload_sign_up_complete", uuid=upload_key))


@app.route("/sign-in")
def sign_in():
    return render_template("sign_in.html")


@app.route("/upload-sign-in", methods=["POST"])
def upload_sign_in():
    """Handle the upload of a file."""
    form = request.form

    print("=== Form Data ===")

    # Target folder for these uploads.
    target = "uploadr/static/test"

    images = []
    for upload in request.files.getlist("file"):
        filename = upload.filename.rsplit("/")[0]
        destination = "/".join([target, filename])
        print("Accept incoming file:", filename)
        print("Save it to:", destination)
        upload.save(destination)

        images.append(dataio.convert_img_to_bytes(destination))

    data = {
        "images": images,
    }

    # POST request
    headers = {"Content-Type": "application/json"}
    url = "http://localhost:9001/api/user/verify"
    r = requests.post(url=url, data=json.dumps(data), headers=headers)

    # response = make_response(
    #     jsonify(
    #         json.loads(r.text)
    #     ),
    #     r.status_code,
    # )
    # response.headers["Content-Type"] = "application/json"

    responses = json.loads(r.text)["responses"]
    responses = [json.loads(response) for response in responses]

    return render_template('sign_in.html', responses=responses)


@app.route("/files/<uuid>")
def upload_sign_up_complete(uuid):
    """The location we send them to at the end of the upload."""

    # Get their files.
    root = "uploadr/static/uploads/{}".format(uuid)
    if not os.path.isdir(root):
        return "Error: UUID not found!"

    files = []
    for file in glob.glob("{}/*.*".format(root)):
        files.append(file)

    meta_data = {}
    images = []
    for file in files:
        if "metadata.txt" in file:
            with open(file) as f:
                meta_data = json.load(f)
        else:
            images.append(dataio.convert_img_to_bytes(file))

    data = {
        "images": images,
        "metadata": meta_data
    }

    # POST request
    headers = {"Content-Type": "application/json"}
    url = "http://localhost:9001/api/user/register"
    r = requests.post(url=url, data=json.dumps(data), headers=headers)

    response = make_response(
        jsonify(
            json.loads(r.text)
        ),
        200,
    )
    response.headers["Content-Type"] = "application/json"

    return response


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))
