import json
import os
import numpy as np
from flask import Blueprint, Flask, make_response, request, jsonify, render_template
import face_recognition
from util import dataio
from PIL import Image
import numpy as np
from collections import defaultdict
import requests


face = Blueprint('face', __name__)


@face.route('pattern', methods=['POST'])
def api_register_pattern():
    data = request.get_json()
    images = data.get('images')

    encodings = []
    face_images = []

    for image in images:
        # convert bytes to array
        image = dataio.convert_bytes_to_numpy_array(image)
        # get face location and face encoding
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)
        # validate
        if len(face_encodings) != 1 or len(face_locations) != 1:
            continue
        face_encoding = face_encodings[0]
        face_location = face_locations[0]
        if type(face_encoding) == np.ndarray:
            face_encoding = face_encoding.tolist()
        # append result
        encodings.append(face_encoding)
        top, right, bottom, left = face_location
        face_image = image[top:bottom, left:right]
        face_images.append(dataio.convert_numpy_array_to_bytes(face_image))

    if not len(encodings):
        return make_response(jsonify({
            "message": "Invalid images",
        }), 400)

    return make_response(jsonify({
        "face_images": face_images,
        "encodings": encodings,
        "message": "Success",
    }), 200)


@face.route('pattern', methods=['PUT'])
def api_verify_pattern():
    data = request.get_json()
    images = data.get('images')

    payload = []
    for image in images:
        # convert byte to numpy array
        unknown_image = dataio.convert_bytes_to_numpy_array(image)
        # get features face
        face_locations = face_recognition.face_locations(unknown_image)
        face_encodings = face_recognition.face_encodings(unknown_image, face_locations)
        face_encodings = [features.tolist() for features in face_encodings if type(features) == np.ndarray]
        d = {"face_images": face_locations,
             "gate_location": np.arange(len(face_encodings)).tolist(),
             "status": [1] * len(face_encodings),
             "encodings": face_encodings
        }
        payload.append(d)

    # POST request
    url = "http://localhost:8999/api/user/pattern"
    r = requests.put(url=url, json=payload)
    response = make_response(
        jsonify(
            json.loads(r.text)
        ),
        r.status_code,
    )
    return response


if __name__ == '__main__':
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
    app.register_blueprint(face, url_prefix='/api/user')
    app.run(host="0.0.0.0", port="8501", debug=True)