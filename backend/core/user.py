from flask import Flask, make_response, request, jsonify
from copy import deepcopy
from flask_cors import CORS
from threading import Thread, Lock
from loguru import logger
from tqdm import tqdm
import matplotlib.pyplot as plt
import tempfile
import matplotlib
import shutil
import requests
import redis
import json
import time
import os

from util.database import connect_db, close_db, get_latest_db
from util.handler import md5, get_timestamp, get_datetime, remove_duplicate
from util.dataio import convert_bytes_to_numpy_array, convert_numpy_array_to_bytes, convert_img_to_bytes
from core.model import NeighborSearch

requests.packages.urllib3.disable_warnings()
matplotlib.use('agg')

# init model directory
model_dir = "./models"
temp_dir = os.path.join(model_dir, os.getenv("MODEL_INIT", "0"))

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
    logger.info("Create checkpoint in {}".format(temp_dir))
    model = NeighborSearch()
    model.fit([])
    model.save(temp_dir)

model = NeighborSearch.load(temp_dir)


DUPLICATE_SCORE = float(os.getenv("DUPLICATE_SCORE", "0.98"))
VISIBLE_FIELDS = os.getenv(
    "VISIBLE_FIELDS",
    "zfullname,zcfg_requester_address_email,zcfg_requester_position,user_id,zfloor_third,zfloor_fourth"
).split(',')


def run(api_host='0.0.0.0', api_port=8999, debug_mode=True, train_interval=10, trainable=True):
    user = Flask(__name__)
    CORS(user)

    r = redis.Redis(
        host=os.getenv("REDIS_HOST", api_host),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=0
    )
    connected = False
    while not connected:
        try:
            r.ping()
            connected = True
            logger.info("Redis connected!")
        except:
            connected = False
            logger.warning("Redis not connected!")
            time.sleep(5)

    current_time = int(time.time())
    r.set("training_version", current_time)
    r.set(f"serving_version_{api_port}", current_time)

    @user.route('/api/user/pattern', methods=['POST'])
    def api_register_pattern():
        """
        inputs:
        {
            "existed": True  # only update
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
                "message": "Invalid format, `zcfg_requester_address_email` or `zcfg_requester_id_passport` not found."
            }), 400)
        
        # get images
        images = data.get("images", [])
        if not isinstance(images, list):
            return make_response(jsonify({
                "message": "Invalid format, please provide list of images."
            }), 400)

        # convert image type
        valid_images = []
        for image in images:
            try:
                # force resize
                image = convert_numpy_array_to_bytes(convert_bytes_to_numpy_array(image))
                valid_images.append(image)
            except:
                logger.info("Can't convert PNG image to JPEG image.")
        images = valid_images

        connected = False
        if len(images) > 0:
            try:
                responses = requests.post(
                    url=os.getenv("MODEL_API", "https://127.0.0.1:8501/api/user/pattern"),
                    json=images, verify=False, timeout=60,
                    headers={"Authorization": "Bearer {}".format(
                        os.getenv("ACCESS_TOKEN", "")
                    )}
                )
                if responses.status_code == 200:
                    responses = json.loads(responses.text)
                else:
                    responses = {}
                connected = True
            except Exception as e:
                logger.error('Generate embedding error: {}'.format(str(e)))
                responses = {}
        else:
            responses = {}
            connected = None

        # generate unique user_id
        user_id = md5("{}_{}".format(id_passport, address_email))
        data["user_id"] = user_id
        data["active"] = data.get("active", False)  # auto deactive
        data["face_images"] = responses.get("face_images", [])
        data["encodings"] = responses.get("encodings", [])
        current_data = deepcopy(data)

        # open connection
        db_conn = connect_db()

        # query user is exist or not
        collection = db_conn["customers"]
        exist_user = collection.find_one({"user_id": user_id})

        if (not exist_user) and data.get("existed"):
            close_db()
            return make_response(jsonify({
                "message": "User not found.",
            }), 200)

        # not need save images (only need face images)
        data = {k: v for k, v in data.items() if k != 'images'}
        if not exist_user:
            collection.insert_one(data)
        else:
            if data.get("existed"):
                data["active"] = exist_user["active"]  # keep current status

            # combine data (only face images and features)
            data["face_images"].extend(exist_user["face_images"])
            data["encodings"].extend(exist_user["encodings"])

            # filter data by duplicate score
            if len(data["encodings"]):
                data["encodings"], ids = remove_duplicate(
                    features=data["encodings"], duplicate_score=DUPLICATE_SCORE
                )
                data["face_images"] = [data["face_images"][i] for i in ids]

            collection.update_one({"user_id": user_id},
                                  {"$set": data})

        # check register or update
        if not exist_user:
            method = "add"
            if not len(images):
                message = "Register success, but empty images."
            elif not len(data["encodings"]):
                message = "Register success, but invalid images."
            else:
                message = "Register success."
        else:
            method = "edit"
            if not len(data["encodings"]):
                message = "Update success, but invalid images."
            else:
                message = "Update success."

        # save logs with current data (not combined)
        log = {k: v for k, v in current_data.items() if k not in ['face_images', 'encodings']}
        log.update({
            "timestamp": get_timestamp(),
            "images": images,
            "message": message,
            "method": method
        })
        collection = db_conn["register_logs"]
        collection.insert_one(log)

        # close connection
        close_db()

        return make_response(jsonify({
            "message": message,
            "connected": connected,
            "user_id": user_id
        }), 200)

    @user.route('/api/user/pattern', methods=['PUT'])
    def api_verify_pattern():
        """
        inputs:
        [
            {
                "encodings": ["<encoding_1>", "<encoding_2>", ...],
                "face_images": ["<face_image_1>", "<face_image_2>", ...],
                "gate_location": [1, 2, ...]
            },
            ...
        ]
        """
        global model

        # Reload model
        if r.get(f"serving_version_{api_port}") != r.get("training_version"):
            r.set(f"serving_version_{api_port}", r.get("training_version"))
            model_version = str(r.get("training_version").decode())
            model = NeighborSearch.load(os.path.join(model_dir, model_version))
            logger.info("Reload model: {} cause: auto train".format(model_version))

        if not len(model.metadata):  # is temp
            model_version = sorted(os.listdir(model_dir))[-1]
            model = NeighborSearch.load(os.path.join(model_dir, model_version))
            logger.info("Reload model: {} cause: temp".format(model_version))

        db_conn = connect_db()
        collection_logs = db_conn["verify_logs"]

        # validate data
        body = request.get_json()
        data = body.get("data")
        matched_score = body.get("matched_score")

        if not len(data):
            return make_response(jsonify({
                "responses": [],
                "message": "Invalid format, data not found.",
            }), 400)

        responses = []
        for d in tqdm(data, desc="Predict"): # for each frame
            preds = model.predict(d['encodings'], matched_score=matched_score)
            for i, pred in enumerate(preds): # for each user in an image
                if not pred["user_id"]:
                    continue
                # add info from request
                for k, v in d.items():
                    try:
                        pred[k] = v[i]
                    except:
                        pred[k] = ''  # fix if not have data
                # save logs
                pred["datetime"] = get_datetime()
                pred = {k: v for k, v in pred.items() if k != '_id'}
                try:
                    collection_logs.insert_one(pred)
                except:
                    pass
                # filter to make response
                pred = {k: v for k, v in pred.items() if k not in ['_id', 'face_images', 'encodings']}
                preds[i] = pred
            responses.append(preds)

        close_db()

        return make_response(jsonify({
                "responses": responses,
                "message": "Verify success.",
            }), 200)

    @user.route('/api/user/pattern', methods=['GET'])
    def api_get_pattern():
        data = request.get_json()
        address_email = data.get("zcfg_requester_address_email", "")
        id_passport = data.get("zcfg_requester_id_passport", "")
        user_id = data.get("user_id", "")
        last_verify = data.get("last_verify", 86400)

        if (not address_email) or (not id_passport):
            return make_response(jsonify({
                "message": "Invalid format, `zcfg_requester_address_email` or `zcfg_requester_id_passport` not found."
            }), 400)

        user_id = user_id or md5("{}_{}".format(id_passport, address_email))

        db_conn = connect_db()
        collection = db_conn["customers"]
        user = collection.find_one({"user_id": user_id})

        if not user:
            return make_response(jsonify({
                "message": "User not found.",
            }), 200)

        from_datetime = get_datetime(get_timestamp() - last_verify)
        verify_cols = db_conn["verify_logs"]
        verify_logs = verify_cols.find({"user_id": user_id, "datetime": {"$gte": from_datetime}})
        verify_logs = [{k: v for k, v in log.items() if k in ['face_images', 'score', 'datetime']} for log in verify_logs]

        scores = [log['score'] for log in verify_logs]
        
        # plot
        plt.figure(figsize=(8, 6))
        plt.hist(scores, color='blue', ec='black', bins=30)
        plt.title("Face score distribution")
        plt.legend(['Counting: {}'.format(len(scores))])
        plt.ylabel('Number of verification')
        plt.xlabel('Score')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg').name
        plt.savefig(temp_file)

        return make_response(jsonify({
            "face_registration": user.get("face_images", []),
            "face_verification": verify_logs,
            "zcfg_requester_address_email": user.get("zcfg_requester_address_email", ""),
            "face_score": convert_img_to_bytes(temp_file)
        }))

    @user.route('/api/user/pattern', methods=['DELETE'])
    def api_delete_pattern():
        """
        Remove all images for user with credentials: email and id passport
        """
        data = request.get_json()
        address_email = data.get("zcfg_requester_address_email", "")
        id_passport = data.get("zcfg_requester_id_passport", "")

        if (not address_email) or (not id_passport):
            return make_response(jsonify({
                "message": "Invalid format, `zcfg_requester_address_email` or `zcfg_requester_id_passport` not found."
            }), 400)

        user_id = md5("{}_{}".format(id_passport, address_email))

        # Delete from database
        db_conn = connect_db()

        collection = db_conn["customers"]
        if not collection.find_one({"user_id": user_id}):
            return make_response(jsonify({
                "message": "User not found.",
            }), 200)

        data["face_images"] = []
        data["encodings"] = []
        collection.update_one({"user_id": user_id},
                              {"$set": data})

        # save log
        method = "delete"
        message = "Delete success."

        log = {
            "timestamp": get_timestamp(),
            "zcfg_requester_address_email": address_email,
            "zcfg_requester_id_passport": id_passport,
            "message": message,
            "method": method
        }
        collection = db_conn["register_logs"]
        collection.insert_one(log)

        close_db()

        return make_response(jsonify({
            "message": message,
            "zcfg_requester_address_email": address_email,
            "zcfg_requester_id_passport": id_passport,
            "user_id": user_id
        }), 200)

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
        lock = Lock()

        db_conn = connect_db()
        customers = db_conn["customers"]
        registry = db_conn["register_logs"]

        last_register = os.path.basename(temp_dir)

        while True:

            if get_latest_db(registry, 'timestamp') != last_register:
                last_register = get_latest_db(registry, 'timestamp')

                lock.acquire()

                data = []
                result = customers.find({'active': True},  {"_id": 0})
                for res in result:
                    for encoding in res["encodings"]:
                        data.append(
                            {
                                'encoding': encoding,
                                'metadata': {k: res.get(k) for k in VISIBLE_FIELDS}
                            }
                        )

                model = NeighborSearch()
                model.fit(data)
                model.save(os.path.join(model_dir, str(last_register)))

                lock.release()

                r.set("training_version", last_register)
            
            else:
                logger.info("Wait new data, current model: {}".format(last_register))

            # Rotation model
            checkpoints = sorted(os.listdir(model_dir))
            num_checkpoints = int(os.getenv("NUM_CHECKPOINT", "10"))
            if len(checkpoints) > num_checkpoints:
                rm_checkpoints = checkpoints[:-num_checkpoints]
                for checkpoint_version in rm_checkpoints:
                    shutil.rmtree(os.path.join(model_dir, checkpoint_version), ignore_errors=True)

            time.sleep(train_interval)

    if trainable:
        Thread(target=auto_train).start()

    logger.info("app listening on port: {}, auto train: {}, debug: {}".format(
            api_port, trainable, debug_mode
        ))

    user.run(
        host=api_host, port=api_port, debug=debug_mode,
        ssl_context=('certs/cert.pem', 'certs/key.pem')
    )
