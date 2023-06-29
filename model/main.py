#!/usr/bin/env python

import os
import cv2
import numpy as np
import onnxruntime
from PIL import Image
from models.scrfd import SCRFD
from models.arcface_onnx import ArcFaceONNX
from scipy.spatial.distance import cdist
from flask import Blueprint, Flask, make_response, request, jsonify
from flask_cors import CORS, cross_origin
from collections import defaultdict
from loguru import logger
import requests
import redis
import time
import json
import os

from util import face_align 
from util.check_zone import IntrusionTask
from util.dataio import send_socket
from util import dataio

os.environ["OMP_NUM_THREADS"] = "1"
onnxruntime.set_default_logger_severity(3)
requests.packages.urllib3.disable_warnings()

CURRENT_DIR = os.getcwd()
detector_model_path = os.path.join(CURRENT_DIR, "models_zoo", 'scrfd_s.onnx')
detector = SCRFD(detector_model_path)
detector.prepare(-1)
embedding_model_path = os.path.join(CURRENT_DIR, "models_zoo", 'arcface_res50.onnx')
rec = ArcFaceONNX(embedding_model_path)
rec.prepare(-1)

backend_api = os.getenv("BACKEND_API", "https://127.0.0.1:8999/api/user/pattern")  # https
redis_conn = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0
)
face = Blueprint('face', __name__)


@face.route('pattern', methods=['POST'])
def api_register_pattern():
    images = request.get_json()

    encodings = []
    face_images = []

    for image in images:
        # convert byte to numpy array BGR
        img = dataio.base64_str_to_cv2(image)  # with rotation if not valid
        if img is None:
            continue

        faces, landmarks = detector.autodetect(img, max_num=1)

        # validate face or not
        if (faces is None) or len(faces) != 1:
            continue

        # validate face size
        bbox = faces[0].astype(np.int32)
        xmin, ymin, xmax, ymax, score = bbox
        if (ymax - ymin < 128) or (xmax - xmin < 128):
            continue

        # get face box
        aimg = face_align.norm_crop(img, landmark=landmarks[0], image_size=128)
        aimgs = [aimg]
        embeddings = rec.get_feat(aimgs).tolist()

        logger.info("Augmentation data register: {}".format(len(aimgs)))

        for face_encoding, face_image in zip(embeddings, aimgs):
            face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)  # save image RGB
            encodings.append(face_encoding)
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

    body = request.get_json()
    images = body.get("images")
    cam_config = body.get("cam_config")

    intrusion_task = IntrusionTask(
        zone=cam_config['zone'], threshold=cam_config.get('intruder_score', 1.0)
    )
    minsize = cam_config.get('face_minsize', 128)

    batch_data = []
    for image in images:
        start_time = time.time()

        # convert byte to numpy array BGR
        img = dataio.convert_bytes_to_numpy_array(image)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        faces, landmarks = detector.autodetect(img, max_num=1)
        if faces is None:
            continue

        data = defaultdict(list)
        faces = faces.astype(np.int32)

        aimgs = []
        gate_ids = []
        for i in range(faces.shape[0]):
            bbox = faces[i]
            xmin, ymin, xmax, ymax, score = bbox
            gate_id = intrusion_task.check_intrusion((xmin, ymin, xmax, ymax))

            if (ymax - ymin < minsize) or (xmax - xmin < minsize) or (gate_id is None):
                continue

            aimg = face_align.norm_crop(img, landmark=landmarks[i], image_size=128)
            aimgs.append(aimg)
            gate_ids.append(gate_id)

        if not len(aimgs):
            continue

        # batch predict
        embeddings = rec.get_feat(aimgs).tolist()

        logger.info(
            "Recognize time: {}s, Detect faces found: {}".format(
                round(time.time() - start_time, 2), faces.tolist()
            )
        )

        for i in range(len(embeddings)):
            data['gate_location'].append(gate_ids[i])
            data['encodings'].append(embeddings[i])
            face_image = cv2.cvtColor(aimgs[i], cv2.COLOR_BGR2RGB)  # save image RGB
            data['face_images'].append(dataio.convert_numpy_array_to_bytes(face_image))

        batch_data.append(data)

    if not len(batch_data):
        return make_response(jsonify({
            "message": "No faces is founded!",
            "response": [],
        }), 401)

    # Verify request
    r = requests.put(
        url=backend_api, verify=False,
        json={
            "data": batch_data,
            "matched_score": cam_config.get("matched_score")
        }
    )

    # Only get response from 1 frame
    response = r.json()['responses'][0]
    message = r.json()['message']
    logger.info(
        "Query time: {}s, Prediction: {}".format(round(r.elapsed.total_seconds(), 2), response)
    )

    # Open gpio
    for each_user in response:
        if not each_user['user_id']:  # unknown user
            continue

        gate_id = each_user['gate_location']
        gate_key = "G{}".format(gate_id)
        gate_value = redis_conn.get(gate_key)

        current_time = int(time.time())
        gate_data = {
            "time": current_time,
            "status": 1  # status 1 is open
        }

        if gate_value is None:  # init
            send_socket(('127.0.0.1', 8888), f"@O{gate_id}")  # send open signal to socket
            redis_conn.set(gate_key, json.dumps(gate_data))  # send status to queue
        else:
            gate_value = json.loads(gate_value.decode())  # get current status
            if not gate_value['status']:  # status 0 is close
                send_socket(('127.0.0.1', 8888), f"@O{gate_id}")
                redis_conn.set(gate_key, json.dumps(gate_data))

    # 1 camera <-> n gates
    return make_response(
        jsonify({"message": message, "response": response}),
        r.status_code
    )


if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    api_port = int(os.getenv("API_PORT", "8501"))
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(face, url_prefix='/api/user')
    app.run(
        host='0.0.0.0', port=api_port,
        debug=debug_mode, ssl_context=("certs/cert.pem", "certs/key.pem")
    )
