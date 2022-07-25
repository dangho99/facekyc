import json

import numpy as np
from flask import Blueprint, make_response, request, jsonify, render_template
import face_recognition
from util import dataio
from PIL import Image
import requests
import redis


face = Blueprint('face', __name__)


@face.route('detection', methods=['POST'])
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

    valid_images = []
    for img in images:
        img = dataio.convert_bytes_to_numpy_array(img)
        face_locations = face_recognition.face_locations(img)
        if len(face_locations) != 1:
            continue
        top, right, bottom, left = face_locations[0]
        face_image = img[top:bottom, left:right]
        face_image = Image.fromarray(face_image)
        face_image = face_image.resize((160, 160))
        face_image = np.asarray(face_image)
        valid_images.append(face_image)

    if not len(valid_images):
        return make_response(jsonify({
            "data": {},
            "message": "Invalid images",
            "message_code": 400
        }), 400)

    # for img in valid_images:
    #     img = Image.fromarray(img)
    #     img.show()

    r = requests.post(url="http://localhost:9501/v1/models/face_recognition/versions/1:predict",
                      data=json.dumps({"instances": np.array(valid_images).tolist()}))

    if r.status_code != 200:
        return make_response(jsonify({
            "data": {},
            "message": "Can't generate latent space",
            "message_code": 400
        }), 400)

    res = json.loads(r.text)
    features = res["predictions"]

    # save to kafka
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
