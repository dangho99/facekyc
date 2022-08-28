from flask import Flask, make_response, request, jsonify, render_template
from threading import Thread, Lock
from tqdm import tqdm
import requests
import redis
import json
import time
import os

from util.database import connect_db, close_db
from keeper.environments import SystemEnv
from core.model import NeighborSearch
from util.hash import md5
from util import dataio


# init model directory
model_dir = SystemEnv.checkpoint_path
if not os.path.exists(model_dir):
    os.makedirs(model_dir)
    print("Create checkpoint in {}".format(model_dir))
model = NeighborSearch.load(model_dir)


def run(api_host='0.0.0.0', api_port=8999, debug=True):
    user = Flask(__name__)
    user.config['DEBUG'] = debug

    r = redis.Redis(host=SystemEnv.host, port=6379, db=0)
    current_time = int(time.time())
    r.set("training_version", current_time)
    r.set("serving_version", current_time)

    lock = Lock()

    @user.route('/api/user/pattern', methods=['POST'])
    def api_register_pattern():
        """
        inputs: 
        {
            "images": [<image_1>, <image_2>, ...],
            "zcfg_requester_comboname": "<username>",
            "zcfg_requester_address_email": "<email>",
            "zcfg_requester_id_passport": "<cccd>",
            ...
        }
        """
        data = request.get_json()

        # validate data
        address_email = data.get("zcfg_requester_address_email", "")
        id_passport = data.get("zcfg_requester_id_passport", "")
        if (not address_email) or (not id_passport):
            return make_response(jsonify({
                "message": "Invalid format, address_email or id_passport not found"
            }), 400)

        # get images
        images = data.get("images", [])

        if len(images) > 0:
            r = requests.post(url=SystemEnv.serving_host, json={"images": images})
            if r.status_code == 200:
                responses = json.loads(r.text)
            else:
                responses = {}
        else:
            responses = {}

        # generate unique user_id
        user_id = md5(address_email + id_passport)
        data["user_id"] = user_id
        data["face_images"] = responses.get("face_images", [])
        data["encodings"] = responses.get("encodings", [])

        # push redis to indexing
        if len(data["encodings"]) > 0:
            r = redis.Redis(host=SystemEnv.host, port=6379, db=0)
            for encoding in data["encodings"]:
                r.rpush("training_data", json.dumps({
                    "metadata": {"user_id": user_id},
                    "encoding": encoding
                }))

        collection = connect_db("customers")
        exist_user = collection.find_one({"user_id": user_id})
        if not exist_user:
            collection.insert_one(data)
        else:
            data["face_images"].extend(exist_user["face_images"])
            data["encodings"].extend(exist_user["encodings"])
            collection.update_one({"user_id": user_id},
                                {"$set": data})
        close_db()

        # make response
        if not exist_user:
            if not len(images):
                return make_response(jsonify({
                    "message": "Register success, but empty images"
                }), 200)
            if not len(data["encodings"]):
                return make_response(jsonify({
                    "message": "Register success, but invalid images"
                }), 200)
            else:
                return make_response(jsonify({
                    "message": "Register success"
                }), 200)
        else:
            if not len(data["encodings"]):
                return make_response(jsonify({
                    "message": "Update success, but invalid images"
                }), 200)
            else:
                return make_response(jsonify({
                    "message": "Update success"
                }), 200)


    @user.route('/api/user/pattern', methods=['PUT'])
    def api_verify_pattern():
        """
        inputs: 
        [
            {
                "encodings": ["<encoding_1>", "<encoding_2>", ...],
                "face_images": ["<face_image_1>", "<face_image_2>", ...],
                "gate_location": [1, 2, ...],
                "status": [1, 1, ...]
            },
            ...
        ]
        """
        global model

        if r.get("serving_version") != r.get("training_version"):
            model = NeighborSearch.load(model_dir)
            r.set("serving_version", r.get("training_version"))

        collection = connect_db("customers")

        data = request.get_json()
        try:
            responses = []
            for d in tqdm(data, desc="Predict"):
                preds = model.predict(d['encodings'])
                """
                preds = [
                    {"user_id": "", "score": 0.},
                    ...
                ]
                """
                for i, pred in enumerate(preds):
                    if not pred["user_id"]:
                        continue

                    record = collection.find_one({"user_id": pred["user_id"]})
                    if not record:
                        pred["user_id"] = "<invalid>"
                        continue

                    # get more info
                    for k, v in record.items():
                        if k in ['images', 'face_images', 'encodings', '_id']: # not need
                            continue
                        pred[k] = v
                    for k, v in d.items():
                        if k == "encodings":
                            continue
                        pred[k] = v[i]
                    
                responses.append(preds)
            ok = True
        except Exception as e:
            print('predict data got error: {}'.format(str(e)))
            responses = []
            ok = False

        close_db()

        return jsonify({
            'responses': responses,
            'ok': ok
        })


    @user.route('/api/user/pattern', methods=['DELETE'])
    def api_reset_pattern():
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return make_response(jsonify({
                "message": "Invalid format, user_id not found",
            }), 400)

        collection = connect_db("customers")
        exist_user = collection.find_one({"user_id": user_id})
        if not exist_user:
            return make_response(jsonify({
                "message": "User is invalid",
            }), 200)

        collection.delete_one({"user_id": user_id})
        close_db()

        return make_response(jsonify({
            "message": "Delete success"
        }), 200)


    def auto_train():
        interval = 5
        while True:
            data = r.lpop("training_data")
            if not data:
                time.sleep(interval)
                continue

            lock.acquire()
            data = json.loads(data)
            model = NeighborSearch.load(model_dir)
            model.partial_fit([data])
            model.save(model_dir)
            lock.release()

            r.set("training_version", int(time.time()))
            time.sleep(interval)

    Thread(target=auto_train).start()
    user.run(host=api_host, port=api_port)
