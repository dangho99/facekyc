from collections import defaultdict
from tqdm import tqdm
import numpy as np
import faiss
import json
import os

from util.logger import get_logger
logger = get_logger("logs")

class NeighborSearch:
    def __init__(self):
        self.duplicate_score = float(os.getenv("DUPLICATE_SCORE", "0.98"))
        self.matched_score = float(os.getenv("MATCHED_SCORE", "0.90"))
        self.k = int(os.getenv("K_MODEL", "5"))
        if os.getenv("METRIC_MODEL") == "cosine":
            self.indexing = faiss.IndexFlatIP(int(os.getenv("DIM_MODEL", "512")))
        elif os.getenv("METRIC_MODEL") == "euclidean":
            self.indexing = faiss.IndexFlatL2(int(os.getenv("DIM_MODEL", "512")))
        else:
            raise ValueError("Metric not found!")
        self.metadata = []

    def fit(self, data):
        if len(data) == 0:
            return
        encodings = []
        metadata = []
        for d in tqdm(data, desc='Training'):
            encodings.append(d['encoding'])
            metadata.append(d['metadata'])
            if len(encodings) >= 100:
                self._fit(encodings, metadata)
                encodings = []
                metadata = []
        if len(encodings) > 0:
            self._fit(encodings, metadata)

    def _fit(self, encodings, metadata):
        if len(encodings) == 0:
            return
        encodings = np.array(encodings, dtype=np.float32)
        encodings = encodings / np.linalg.norm(encodings, axis=1, keepdims=True)
        ranges, distances, indexes = self.indexing.range_search(encodings, self.duplicate_score)
        vs = []
        dt = []
        for i, (v, d) in enumerate(zip(encodings, metadata)):
            ids = list(indexes[ranges[i]:ranges[i+1]])
            if ids:
                conflicted = False
                for idx in ids:
                    if self.metadata[idx]['user_id'] != d['user_id']:
                        conflicted = True
                        break
                if not conflicted and ranges[i+1] - ranges[i] < self.k:
                    vs.append(v)
                    dt.append(d)
            else:
                vs.append(v)
                dt.append(d)
        if len(vs) > 0:
            self.indexing.add(np.array(vs).astype(np.float32))
            self.metadata.extend(dt)

    def partial_fit(self, data):
        self.fit(data)

    def predict(self, encodings):
        if len(encodings) == 0:
            return []
        encodings = np.array(encodings, dtype=np.float32)
        encodings = encodings / np.linalg.norm(encodings, axis=1, keepdims=True)
        ranges, distances, indexes = self.indexing.range_search(encodings, self.matched_score)
        result = []
        for i in range(len(encodings)):
            ds = distances[ranges[i]:ranges[i+1]]
            ids = indexes[ranges[i]:ranges[i+1]]
            if len(ds) > 1:
                ds, ids = zip(*sorted(zip(ds, ids), key=lambda x: x[0], reverse=True))
            if not len(ds):
                result.append({"user_id": "", "score": 0.})
                continue
            stats = defaultdict(list)
            for dist, idx in zip(ds, ids):
                stats[self.metadata[idx]['user_id']].append(dist)
            for k, v in stats.items():
                stats[k] = float(np.sum(v) / (len(v) + 1e-9))
            user_id, score = max(stats.items(), key=lambda x: x[1])
            result.append({"user_id": user_id, "score": round(score, 2)})
        return result

    def save(self, path):
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
