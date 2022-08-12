import json

import numpy as np
import redis
import requests
from flask import Blueprint, make_response, request, jsonify, render_template

from util import dataio
from keeper.environments import SystemEnv
import pymongo


user = Blueprint('user', __name__)


@user.route('register', methods=['POST'])
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
    if (not user_id) or (not images):
        return make_response(jsonify({
            "message": "Invalid format, user_id or images not found"
        }), 400)

    # connect to mongodb
    client = pymongo.MongoClient("mongodb://admin:pass@localhost:27017/")
    db = client["kotora"]
    collection = db["customers"]

    # validate exist user or not
    is_exist_user = collection.find_one({"user_id": user_id})
    if is_exist_user:
        return make_response(jsonify({
            "message": "User is exist"
        }), 400)

    # get face encodings
    """
    inputs:
    {
        "images": [<image_1>, <image_2>, ...],
        "user_id": <user_id>
    }
    outputs:
    {
        "face_images": [<face_image_1>, <face_image_2>, ...],
        "encodings": [<encoding_1>, <encoding_2>, ...],
        "user_id": <user_id>
    }
    """
    inputs = {"images": images, "user_id": user_id}
    r = requests.post(url=SystemEnv.serving_host, json=inputs)
    if r.status_code != 200:
        return make_response(r.text, r.status_code)
    outputs = json.loads(r.text)

    # insert to mongodb if new user
    record = {
        "user_id": user_id,
        "user_name": user_name,
        "phone_number": phone_number,
        "face_images": outputs["face_images"],
        "encodings": outputs["encodings"]
    }
    collection.insert_one(record)

    # push redis to training
    r = redis.Redis(host=SystemEnv.redis_host, port=6379, db=0)
    training_data = {
        "user_id": user_id,
        "encodings": outputs["encodings"]
    }
    r.rpush("training_data", json.dumps(training_data))

    return make_response(jsonify({
        "message": "Register success"
    }), 200)


@user.route('pattern', methods=['DELETE'])
def api_reset_pattern():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return make_response(jsonify({
            "data": {},
            "message": "Invalid format, user_id can not be empty",
            "message_code": 400
        }), 400)

    from database.user import User
    _user = User.query.filter_by(user_id=user_id).first()

    if not _user:
        return make_response(jsonify({
            "data": {},
            "message": "User is invalid",
            "message_code": 10001
        }), 401)

    result = Core.reset(user_id=user_id)

    if not result:
        return make_response(jsonify({
            "data": {},
            "message": "Database is busy",
            "message_code": 10003
        }), 401)

    Monitor.capture(
        user_id=user_id,
        is_success=result,
        event_type="reset_pattern",
        data={}
    )

    return render_template(
        "api_reset_pattern_response.json.jinja",
        message="Success",
        message_code=200
    )


@user.route('pattern', methods=['PUT'])
def api_verify_pattern():
    data = request.get_json()
    user_id = data.get("user_id")
    features = data.get("data")

    if (not user_id) or (not features):
        return make_response(jsonify({
            "data": {},
            "message": "Invalid format, user_id & data can not be empty",
            "message_code": 400
        }), 400)

    from database.user import User
    _user = User.query.filter_by(user_id=user_id).first()

    if not _user:
        return make_response(jsonify({
            "data": {},
            "message": "User is invalid",
            "message_code": 10001
        }), 401)

    matched_score = Core.verify(user_id=user_id, features=features)
    matched_score = np.mean(matched_score)

    is_success = bool(matched_score < SystemEnv.matching_threshold)

    if matched_score != -1:
        Monitor.capture(
            user_id=user_id,
            is_success=is_success,
            event_type="verify_pattern",
            predicted="Owner" if is_success else "Imposter",
            score=matched_score,
            data=features
        )

    if is_success:
        return render_template(
            "api_verify_pattern_response.json.jinja",
            matched_score=matched_score,
            message="Pattern is valid",
            message_code=10007
        )

    return render_template(
        "api_verify_pattern_response.json.jinja",
        matched_score=matched_score,
        message="Pattern is invalid",
        message_code=10006
    )
