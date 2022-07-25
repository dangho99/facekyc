import redis
import time
from core.model import NeighborSearch
from core import server
import json


class Trainer:
    def __init__(self):
        self.model = None

    def new_train(self, model_dir):
        # get data
        r = redis.Redis(host="localhost", port=6379, db=0)
        data_train = r.lrange("face_features", 0, -1)
        data_train = [json.loads(d) for d in data_train]
        # r.delete("face_features")
        # r.flushall()

        # init model
        model = NeighborSearch()
        model.fit(data_train)
        model.save(model_dir)
        self.model = model
        print("Training from scratch ok.")

    def re_train(self, model_dir, data):
        model = self.model
        model.partial_fit(data)
        model.save(model_dir)
        print("Re-training ok.")
        return

if __name__ == '__main__':
    trainer = Trainer()
    server.run_train(trainer, interval=5)
