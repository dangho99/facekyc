#!/usr/bin/env python

import os
import cv2
import numpy as np
import onnxruntime
from PIL import Image
import datetime
from models.scrfd import SCRFD
from models.arcface_onnx import ArcFaceONNX
from scipy.spatial.distance import cdist
from flask import Blueprint, Flask, make_response, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_bcrypt import Bcrypt
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

RSA_PRIVATE = """
-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
"""

RSA_PUBLIC = """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAu5rmF7VGPb60Ol/yqZP0
pgyuMmSyANVpMJsdxMVDe8XF/pJQdph1RKgwA0gUt+1rhsyUgEy8/ULFvkSLWixH
eCOZhSk3UahpKNQsvkBvq86LXda2AvqHku8xW6oAs/LKJE1H+Lm8SY2XYEH2nplM
SjE07FpQ7ihUCLzFe7XQvZBsvmKNftO1CwlAW5iyPliFh7sSmFVda8gzsJhJDUJT
CaXUfqhpGXeQswYm4CvSHIGCjWIdTNeHV2vJ4qg8niQwtoeF1tobESHa4TeoKiHw
+g8uv15opfXb6ekJd+CVo1egNkMg6qO73dY/1qLWHAicEZVi9GsJAqw2/A0iiPv3
IWLz7k5d3DTyqRteKPfqANcxbyLmgTp5XHbbWxDsnTRBMdkn62YFtopQvaqKgOd+
uhTSDK/2QQRqXDB+40DiHVuI8TcABkBsrlEt9nOhULtk9VZqJ8pfbxS7o4zv72vY
tDAjAwOqmvHTAEHekNCeOxyMUDDOKVxSSeYyhUJOElh94DUK6ihDWU7ibSO0fX0f
9LKBi+8qVWUQB9nc0kN1DB7/F7CPtLPk1T4gWY4KcfQq/2td5xEdCocyX63fTzUU
loPXo9ilAtrALzGv5yeqUjbCGwpvXq/6xxh8NTRL4zekRhGExrUUCjoIllEbc5WY
7dVfJPNtlWSFN3LqAz/WFdcCAwEAAQ==
-----END PUBLIC KEY-----
"""

CURRENT_DIR = os.getcwd()
detector_model_path = os.path.join(CURRENT_DIR, "models_zoo", 'scrfd_s.onnx')
detector = SCRFD(detector_model_path)
detector.prepare(0)
embedding_model_path = os.path.join(CURRENT_DIR, "models_zoo", 'arcface_res50.onnx')
rec = ArcFaceONNX(embedding_model_path)
rec.prepare(0)

backend_api = os.getenv("BACKEND_API", "https://127.0.0.1:8999/api/user/pattern")  # https
redis_conn = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0
)
check_location = os.getenv('CHECK_LOCATION', 'True').lower() == 'true'
gate_interval = float(os.getenv("GATE_INTERVAL", "3.0"))


face = Blueprint('face', __name__)


@face.route('pattern', methods=['POST'])
@jwt_required()
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
@jwt_required()
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
    valid_response = []
    for each_user in response:
        if not each_user['user_id']:  # unknown user
            continue

        if not each_user.get(cam_config['location']) and check_location:  # access denied
            logger.info("Access denied: {}".format(each_user))
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
            if (not gate_value['status']) and (current_time - gate_value['time'] >= gate_interval):  # status 0 is close
                send_socket(('127.0.0.1', 8888), f"@O{gate_id}")
                redis_conn.set(gate_key, json.dumps(gate_data))

        valid_response.append(each_user)

    logger.info("Valid Prediction: {}".format(valid_response))

    # 1 camera <-> n gates
    return make_response(
        jsonify({"message": message, "response": valid_response}),
        r.status_code
    )


@face.route('create-dev-token', methods=['POST'])
def create_dev_token():
    auth = request.authorization
    body = request.get_json()
    if not isinstance(body, dict):
        body = {}

    days = body.get('days', 0)
    hours = body.get('hours', 0)
    minutes = body.get('minutes', 0)
    seconds = body.get('seconds', 0)

    expired_time = None
    if days or hours or minutes or seconds:
        expired_time = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    if auth and auth.username == os.getenv('API_USER', 'masteradmin@kotora.vn') and bcrypt.check_password_hash(
        os.getenv('API_SECRET', '$2b$12$TxHf.cxpHVwWCHad1oGYGuuDEZDDxTTSZo5mjNdJv.QSVuEs4QIpG'), auth.password
    ):
        token = create_access_token(identity=auth.username, expires_delta=expired_time)
        return make_response(jsonify({
            'message': 'Verify success!',
            'token': token
        }), 302)

    return make_response(jsonify({
        'message': 'Could not verify!'
    }), 401)


if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    api_port = int(os.getenv("API_PORT", "8501"))
    app = Flask(__name__)
    app.register_blueprint(face, url_prefix='/api/user')

    cors = CORS(app)
    jwt = JWTManager(app)
    bcrypt = Bcrypt(app)

    app.config['JWT_PUBLIC_KEY'] = RSA_PUBLIC
    app.config['JWT_PRIVATE_KEY'] = RSA_PRIVATE
    app.config['JWT_ALGORITHM'] = 'RS256'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=400)  # 1 year 1 month

    app.run(
        host='0.0.0.0', port=api_port,
        debug=debug_mode, ssl_context=("certs/cert.pem", "certs/key.pem")
    )
