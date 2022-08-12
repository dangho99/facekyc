from collections import defaultdict
from tqdm import tqdm
import numpy as np
import faiss
import json
import time
import os
from keeper.environments import SystemEnv


class NeighborSearch:
    def __init__(self):
        self.matched_score = SystemEnv.matched_score
        self.duplicate_score = SystemEnv.duplicate_score
        self.batch_size = 100
        self.k = SystemEnv.k
        self.indexing = faiss.IndexFlatIP(SystemEnv.n_dims)
        self.metadata = []

    def fit(self, data):
        if len(data) == 0:
            return
        features = []
        metadata = []
        for d in tqdm(data, desc='Training'):
            features.append(d['features'])
            metadata.append(d['metadata'])
            if len(features) >= self.batch_size:
                self._fit(features, metadata)
                features = []
                metadata = []
        if len(features) > 0:
            self._fit(features, metadata)

    def _fit(self, features, metadata):
        if len(features) == 0:
            return
        features = np.array(features, dtype=np.float32)
        features = features / np.linalg.norm(features, axis=1, keepdims=True)
        ranges, distances, indexes = self.indexing.range_search(features, self.duplicate_score)
        vs = []
        dt = []
        for i, (v, d) in enumerate(zip(features, metadata)):
            ids = list(indexes[ranges[i]:ranges[i+1]])
            if ids:
                conflicted = False
                for idx in ids:
                    if self.metadata[idx]['userid'] != d['userid']:
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

    def predict(self, features):
        if len(features) == 0:
            return []
        features = np.array(features, dtype=np.float32)
        features = features / np.linalg.norm(features, axis=1, keepdims=True)
        ranges, distances, indexes = self.indexing.range_search(features, self.matched_score)
        result = []
        for i in range(len(features)):
            ds = distances[ranges[i]:ranges[i+1]]
            ids = indexes[ranges[i]:ranges[i+1]]
            if len(ds) > 1:
                ds, ids = zip(*sorted(zip(ds, ids), key=lambda x: x[0], reverse=True))
            if not len(ds):
                result.append({"userid": "", "score": 0.})
                continue
            stats = defaultdict(list)
            for dist, idx in zip(ds, ids):
                stats[self.metadata[idx]['userid']].append(dist)
            for k, v in stats.items():
                stats[k] = float(np.sum(v) / (len(v) + 1e-9))
            userid, score = max(stats.items(), key=lambda x: x[1])
            result.append({"userid": userid, "score": round(score, 2)})
        return result

    def save(self, path):
        faiss.write_index(self.indexing, path + '.indexing')
        with open(path + '.metadata', 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f)
        print("Save model success to: {}".format(os.path.dirname(path)))

    @staticmethod
    def load(path):
        model = NeighborSearch()
        try:
            model.indexing = faiss.read_index(path + '.indexing')
            with open(path + '.metadata') as f:
                model.metadata = json.load(f)
        except Exception as e:
            print("Load model failed from {}, because: {}".format(path, str(e)))
        return model
