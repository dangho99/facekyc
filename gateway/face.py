import json
import numpy as np
from flask import Blueprint, make_response, request, jsonify, render_template
import face_recognition
from util import dataio
from PIL import Image
from collections import defaultdict
import requests
import redis


face = Blueprint('face', __name__)


@face.route('register', methods=['POST'])
def api_register_pattern():
    data = request.get_json()
    images = data.get('images')
    metadata = data.get('metadata')
    userid = metadata.get('userid')

    if (not userid) or (not len(images)):
        return make_response(jsonify({
            "data": {},
            "message": "Invalid format, userid & images can not be empty",
            "message_code": 400
        }), 400)

    features = []
    for img in images:
        img = dataio.convert_bytes_to_numpy_array(img)
        face_encoding = face_recognition.face_encodings(img)
        if len(face_encoding) != 1:
            continue
        face_encoding = face_encoding[0]
        if type(face_encoding) == np.ndarray:
            face_encoding = face_encoding.tolist()
        features.append(face_encoding)

    if not len(features):
        return make_response(jsonify({
            "data": {},
            "message": "Invalid images",
            "message_code": 400
        }), 400)

    # save to queue
    r = redis.Redis(host="localhost", port=6379, db=0)
    for feat in features:
        dummy = {"features": feat, "metadata": metadata}
        r.rpush("face_features", json.dumps(dummy))

    return make_response(jsonify({
        "features": features,
        "metadata": metadata,
        "message": "Success",
        "message_code": 200
    }), 200)


@face.route('verify', methods=['POST'])
def api_verify_pattern():
    data = request.get_json()
    images = data.get('images')

    result = []
    for image in images:
        # convert byte to numpy array
        unknown_image = dataio.convert_bytes_to_numpy_array(image)
        # get features face
        face_locations = face_recognition.face_locations(unknown_image)
        face_encodings = face_recognition.face_encodings(unknown_image, face_locations)
        face_encodings = [features.tolist() for features in face_encodings if type(features) == np.ndarray]
        d = {"image": image,
             "locations": face_locations,
             "features": face_encodings
        }
        result.append(d)
    
    # POST request
    headers = {"Content-Type": "application/json"}
    url = "http://localhost:9003/api/predict"
    r = requests.post(url=url, data=json.dumps(result), headers=headers)
    
    response = make_response(
        jsonify(
            json.loads(r.text)
        ),
        r.status_code,
    )
    response.headers["Content-Type"] = "application/json"

    return response