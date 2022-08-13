from flask import request, jsonify, Flask
from threading import Thread, Lock
import time
import redis
import json
from tqdm import tqdm
import os
import pymongo
from keeper.environments import SystemEnv
from core.model import NeighborSearch


def run(model_dir, api_host='0.0.0.0', api_port=9000, debug=True):
    app = Flask(__name__)
    app.config['DEBUG'] = debug
    lock = Lock()

    r = redis.Redis(host=SystemEnv.host, port=6379, db=0)
    current_time = int(time.time())
    r.set("training_version", current_time)
    r.set("serving_version", current_time)
    interval = 5

    client = pymongo.MongoClient("mongodb://admin:pass@{}:27017/".format(SystemEnv.host))
    db = client["kotora"]
    collection = db["customers"]

    @app.route('/api/model/predict', methods=['POST'])
    def predict():
        global model

        if r.get("serving_version") != r.get("training_version"):
            model = NeighborSearch.load(model_dir)
            r.set("serving_version", r.get("training_version"))

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
                for pred in preds:
                    if not pred["user_id"]:
                        pred["user_id"] = "<unk>"
                        continue

                    record = collection.find_one({"user_id": pred["user_id"]})
                    if not record:
                        pred["user_id"] = "<invalid>"
                        continue

                    # get more info
                    pred["user_name"] = record["user_name"]
                    pred["phone_number"] = record["phone_number"]
                responses.append(preds)
            ok = True
        except Exception as e:
            print('predict data got error: {}'.format(str(e)))
            responses = []
            ok = False

        return jsonify({
            'responses': responses,
            'ok': ok
        })

    def auto_train():
        while True:
            data = r.lpop("training_data")
            if not data:
                print("Empty data")
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
    app.run(host=api_host, port=api_port)


if __name__ == '__main__':
    model_dir = SystemEnv.checkpoint_path
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print("Create checkpoint in {}".format(model_dir))

    model = NeighborSearch.load(model_dir)
    run(model_dir=model_dir, api_host="0.0.0.0", api_port=9000, debug=True)