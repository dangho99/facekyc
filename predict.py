import json
import os

from core import server
from core.model import NeighborSearch


class Predictor:
    def __init__(self, model_dir=None):
        self.model = NeighborSearch.load(model_dir)

    def predict(self, data):
        preds = self.model.predict(data)
        return preds


if __name__ == '__main__':
    model = Predictor(model_dir="./checkpoint/model")
    server.run(model)