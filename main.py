import json

import numpy as np
import redis
import requests
from flask import Blueprint, Flask, make_response, request, jsonify, render_template

from util import dataio
from keeper.environments import SystemEnv
import pymongo


user = Blueprint('user', __name__)


@user.route('pattern', methods=['POST'])
def api_register_pattern():
    """
    inputs: 
    {
        "images": [<image_1>, <image_2>, ...],
        "metadata": {
            "user_id": <user_id>,
            "user_name": <user_name>,
            "phone_number": <phone_number>,
            ...
        }
    }
    """
    data = request.get_json()
    if not data:
        return make_response(jsonify({
            "message": "Invalid format, data not found"
        }), 400)

    # get images -> send to face-recognition model
    images = data.get("images")

    # get metadata -> save to mongodb
    metadata = data.get('metadata')
    user_id = metadata.get('user_id')
    user_name = metadata.get('user_name')
    phone_number = metadata.get('phone_number')

    # validate data
    if not user_id:
        return make_response(jsonify({
            "message": "Invalid format, user_id not found"
        }), 400)

    # get face encodings
    """
    inputs: {
        "images": [<image_1>, <image_2>, ...]
    }
    outputs: {
        "face_images": [<face_image_1>, <face_image_2>, ...],
        "encodings": [<encoding_1>, <encoding_2>, ...],
        "message": "<message>"
    }
    """
    if len(images) > 0:
        inputs = {"images": images}
        r = requests.post(url=SystemEnv.serving_host, json=inputs)
        if r.status_code != 200:
            return make_response(r.text, r.status_code)
        outputs = json.loads(r.text)
    else:
        outputs = {}

    # connect to mongodb
    client = pymongo.MongoClient("mongodb://admin:pass@{}:27017/".format(SystemEnv.host))
    db = client["kotora"]
    collection = db["customers"]

    record = {
        "user_id": user_id,
        "user_name": user_name,
        "phone_number": phone_number,
        "face_images": outputs.get("face_images", []),
        "encodings": outputs.get("encodings", [])
    }
    # validate exist user or not
    exist_user = collection.find_one({"user_id": user_id})
    if exist_user:
        collection.update_one(
            {"user_id": user_id},
            { "$set": record }
        )
        message = "Update success"
    else:
        collection.insert_one(record)
        message = "Register success"

    # not training when encodings is empty
    if not len(record["encodings"]):
        return make_response(jsonify({
            "message": message,
            "training": False
        }), 200)

    # push redis -> prepare training
    r = redis.Redis(host=SystemEnv.host, port=6379, db=0)
    for encoding in record["encodings"]:
        r.rpush("training_data", json.dumps({
            "metadata": {"user_id": user_id},
            "encoding": encoding
        }))

    return make_response(jsonify({
        "message": message,
        "training": True
    }), 200)


@user.route('pattern', methods=['DELETE'])
def api_reset_pattern():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return make_response(jsonify({
            "message": "Invalid format, user_id not found",
        }), 400)

    client = pymongo.MongoClient("mongodb://admin:pass@{}:27017/".format(SystemEnv.host))
    db = client["kotora"]
    collection = db["customers"]

    exist_user = collection.find_one({"user_id": user_id})
    if not exist_user:
        return make_response(jsonify({
            "message": "User is invalid",
        }), 400)

    collection.delete_one({"user_id": user_id})
    return make_response(jsonify({
        "message": "Delete success"
    }), 200)


if __name__ == '__main__':
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
    app.register_blueprint(user, url_prefix='/api/user')
    app.run(host="0.0.0.0", port="8999", debug=True)
