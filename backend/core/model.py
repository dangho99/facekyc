from collections import defaultdict
from loguru import logger
from tqdm import tqdm
import numpy as np
import faiss
import json
import os


class NeighborSearch:
    def __init__(self, matched_score=0.7, dim=512, k=10):
        self.matched_score = matched_score
        self.k = k
        self.indexing = faiss.IndexFlatL2(dim)
        self.metadata = []

    def fit(self, data):
        if len(data) == 0:
            return
        encodings = []
        metadata = []
        for d in tqdm(data, desc='Training'):
            encodings.append(d['encoding'])
            metadata.append(d['metadata'])
        self._fit(encodings, metadata)

    def _fit(self, encodings, metadata):
        if len(encodings) == 0:
            return
        encodings = np.array(encodings, dtype=np.float32)
        encodings = encodings / np.linalg.norm(encodings, axis=1, keepdims=True)
        self.indexing.add(encodings)
        self.metadata.extend(metadata)

    def predict(self, encodings, matched_score=None):
        # get score to search
        matched_score = matched_score or self.matched_score
        if len(encodings) == 0:
            return []
        encodings = np.array(encodings, dtype=np.float32)
        encodings = encodings / np.linalg.norm(encodings, axis=1, keepdims=True)
        distances, indexes = self.indexing.search(encodings, self.k)
        result = []
        for i in range(len(encodings)):
            score = distances[0]
            res = self.metadata[indexes[0]]
            res['score'] = score
            result.append(res)

            logger.info("Found user: {} {}, Score: {}, Prediction: {}".format(
                res.get('user_id'), res.get('zcfg_requester_address_email'), res['score']
            ))

        return result

    def save(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

        faiss.write_index(self.indexing, os.path.join(path, "model.index"))
        with open(os.path.join(path, "model.meta"), 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f)
        logger.info("Save model success to: {}".format(path))

    @staticmethod
    def load(path):
        model = NeighborSearch()
        try:
            model.indexing = faiss.read_index(os.path.join(path, "model.index"))
            with open(os.path.join(path, "model.meta")) as f:
                model.metadata = json.load(f)
            logger.info("Load model success from: {}".format(path))
        except Exception as e:
            logger.info("Load model failed from {}, because: {}".format(path, str(e)))
        return model
