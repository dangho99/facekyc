from flask import request, jsonify, Flask
from threading import Thread
import time
import os
from queue import Queue
from threading import Lock
from .model import NeighborSearch
import queue


def run(model):
    app = Flask(__name__)
    app.config['DEBUG'] = True

    @app.route('/api/predict', methods=['POST'])
    def predict():
        data = request.get_json()
        try:
            responses = model.predict(data)
            ok = True
        except Exception as e:
            print('predict data got error: {}'.format(str(e)))
            responses = []
            ok = False

        return jsonify({
            'responses': responses,
            'ok': ok
        })

    @app.route('/api/v2/get-nearest-neighbors', methods=['POST'])
    def get_nearest_neighbors():
        data = request.get_json()
        try:
            responses, buckets = model.get_nearest_neighbors(data)
        except Exception as e:
            print(str(e))
            return jsonify({
                'k-nearest-neighbors': [],
                'summary': []
            })
        return jsonify({
            'k-nearest-neighbors': responses,
            'summary': buckets
        })
    app.run(host='0.0.0.0', port=9003)


def run_train(trainer, interval=60):
    app = Flask(__name__)
    app.config['DEBUG'] = True
    queue_task = Queue()
    lock = Lock()

    @app.route('/api/train', methods=['POST'])
    def train_api():
        try:
            data = request.json
            if queue_task.empty() and not lock.locked():
                if len(data) > 0:
                    queue_task.put(('re_train', data))
                else:
                    queue_task.put(('new_train', []))
            ok = True
        except Exception as e:
            print('trigger training got error: %s' % str(e))
            ok = False

        return jsonify({
            'ok': ok
        })

    def auto_train():
        while True:
            try:
                print("Wait task")
                try:
                    task = queue_task.get(block=True, timeout=interval)
                except queue.Empty:
                    task = None
                except Exception as e:
                    print(e)
                    continue
                lock.acquire()
                model_dir = "./checkpoint/model"

                try:
                    if task is None:
                        print('Start auto train.')
                        trainer.new_train(model_dir)
                    else:
                        print("Request train.")
                        action, args = task
                        if action == 're_train':
                            trainer.re_train(model_dir, args)
                        else:
                            trainer.new_train(model_dir)
                    print("Done task.")
                except Exception as e:
                    print("Failed task, because: {}".format(str(e)))

                lock.release()
                time.sleep(5)
            except SystemExit:
                break

    Thread(target=auto_train).start()
    app.run(host='0.0.0.0', port=9002)
