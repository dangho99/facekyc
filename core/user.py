from flask import Flask, make_response, request, jsonify
from flask_cors import CORS
from threading import Thread, Lock
from tqdm import tqdm
import requests
import redis
import json
import time
import os

from util.logger import get_timestamp, get_logger
from util.database import connect_db, close_db
from keeper.environments import SystemEnv
from core.model import NeighborSearch
from util.hash import md5

requests.packages.urllib3.disable_warnings()
logger = get_logger("logs")

# init model directory
model_dir = SystemEnv.checkpoint_path
if not os.path.exists(model_dir):
    os.makedirs(model_dir)
    logger.info("Create checkpoint in {}".format(model_dir))
model = NeighborSearch.load(model_dir)


def run(api_host='0.0.0.0', api_port=8999, debug=True):
    user = Flask(__name__)
    CORS(user)
    user.config['DEBUG'] = debug

    r = redis.Redis(host=SystemEnv.host, port=6379, db=0)
    connected = False
    while not connected:
        try:
            r.ping()
            connected = True
            logger.info("Successfully connected to Redis at {}:6379".format(SystemEnv.host))
        except:
            connected = False
            logger.info("Redis connection error at {}:6379".format(SystemEnv.host))
            time.sleep(30)

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
        if not isinstance(images, list):
            return make_response(jsonify({
                "message": "Invalid format, please provide list of images"
            }), 400)

        if len(images) > 0:
            try:
                responses = requests.post(url=SystemEnv.serving_host, json=images, verify=False)
                if responses.status_code == 200:
                    responses = json.loads(responses.text)
                else:
                    responses = {}
                connected = True
            except Exception as e:
                logger.info('Generate embedding %s got error: %s' % (str(images), str(e)))
                responses = {}
                connected = False
        else:
            responses = {}
            connected = False

        # generate unique user_id
        user_id = md5("{}_{}".format(id_passport, address_email))
        data["user_id"] = user_id
        data["face_images"] = responses.get("face_images", [])
        data["encodings"] = responses.get("encodings", [])

        # push redis to indexing
        if len(data["encodings"]) > 0:
            for encoding in data["encodings"]:
                r.rpush("training_data",
                    json.dumps(
                        {
                            "metadata": {
                                "user_id": user_id,
                                "zcfg_requester_comboname": data.get("zcfg_requester_comboname", ""),
                                "zcfg_requester_phone_number": data.get("zcfg_requester_phone_number", ""),
                                "zcfg_requester_address_email": address_email,
                                "zcfg_requester_id_passport": id_passport
                            },
                            "encoding": encoding
                        }
                    )
                )

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
            method = "add"
            if not len(images):
                message = "Register success, but empty images"
            elif not len(data["encodings"]):
                message = "Register success, but invalid images"
            else:
                message = "Register success"
        else:
            method = "edit"
            if not len(data["encodings"]):
                message = "Update success, but invalid images"
            else:
                message = "Update success"

        # save logs
        log = {k: v for k, v in data.items() if k not in ['face_images', 'encodings']}
        log.update({
            "timestamp": get_timestamp(),
            "images": images,
            "message": message,
            "method": method
        })
        collection = connect_db("register_logs")
        collection.insert_one(log)
        close_db()

        return make_response(jsonify({
            "message": message,
            "connected": connected
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

        data = request.get_json()
        try:
            responses = []
            for d in tqdm(data, desc="Predict"):
                preds = model.predict(d['encodings'])
                responses.append(preds)
            ok = True
        except Exception as e:
            logger.info('Predict data %s got error: %s' % (str(data), str(e)))
            responses = []
            ok = False

        return jsonify({
            'responses': responses,
            'ok': ok
        })

    @user.route('/api/user/pattern', methods=['DELETE'])
    def api_reset_pattern():
        data = request.get_json()
        address_email = data.get("zcfg_requester_address_email", "")
        id_passport = data.get("zcfg_requester_id_passport", "")

        if (not address_email) or (not id_passport):
            return make_response(jsonify({
                "message": "Invalid format, address_email or id_passport not found"
            }), 400)

        user_id = md5("{}_{}".format(id_passport, address_email))

        collection = connect_db("customers")
        exist_user = collection.find_one({"user_id": user_id})
        if not exist_user:
            return make_response(jsonify({
                "message": "User is invalid",
            }), 200)

        collection.delete_one({"user_id": user_id})
        close_db()

        return make_response(jsonify({
            "message": "Delete success",
            "email": address_email,
            "id_passport": id_passport
        }), 200)

    @user.route('/api/user/monitor', methods=['PUT'])
    def api_monitor_user():
        """
        api: add verify logs
        """
        data = request.get_json()
        collection = connect_db("verify_logs")
        collection.insert_many(data)

    @user.route('/api/user/monitor', methods=['GET'])
    def api_monitor_user():
        data = request.get_json()
        responses = {}

        zstart_date = data.get('zstart_date', '')
        zend_date = data.get('zend_date', '')
        if zstart_date:
            data['zstart_date'] = {"$gte": zstart_date}
        if zend_date:
            data['zend_date'] = {"$lte": zend_date}

        for collection_name in ["register_logs", "verify_logs"]:
            collection = connect_db(collection_name)
            responses[collection_name] = []
            for record in collection.find(data, {"_id": 0}):
                responses[collection_name].append(record)
        close_db()
        return make_response(jsonify(responses), 200)

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

    Thread(target=auto_train).start()
    user.run(
        host=api_host,
        port=api_port,
        ssl_context=("./certs/cert.pem", "./certs/key.pem")
    )
