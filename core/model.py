from tqdm import tqdm
import numpy as np
import faiss
import json
import time
import os

from keeper.environments import SystemEnv


class NeighborSearch:
    def __init__(self):
        self.duplicate_score = SystemEnv.duplicate_score
        self.k = SystemEnv.k
        if SystemEnv.distance_metric == "cosine":
            self.indexing = faiss.IndexFlatIP(SystemEnv.n_dims)
        elif SystemEnv.distance_metric == "euclidean":
            self.indexing = faiss.IndexFlatL2(SystemEnv.n_dims)
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
        distances, indexes = self.indexing.search(encodings, self.k)
        result = []
        for ds, ids in zip(distances, indexes):
            res = []
            for dist, idx in zip(ds, ids):
                res.append({"score": round(float(dist), 4), **self.metadata[idx]})
            result.append(res)
        return result

    def save(self, path):
        faiss.write_index(self.indexing, os.path.join(path, "model.index"))
        with open(os.path.join(path, "model.meta"), 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f)
        print("Save model success to: {}".format(path))

    @staticmethod
    def load(path):
        model = NeighborSearch()
        try:
            model.indexing = faiss.read_index(os.path.join(path, "model.index"))
            with open(os.path.join(path, "model.meta")) as f:
                model.metadata = json.load(f)
            print("Load model success from: {}".format(path))
        except Exception as e:
            print("Load model failed from {}, because: {}".format(path, str(e)))
        return model
