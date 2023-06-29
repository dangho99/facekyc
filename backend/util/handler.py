from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import numpy as np
import hashlib
import time


def md5(s: str):
    s = hashlib.md5(s.encode()).hexdigest()
    return s


def get_datetime(timestamp=None):
    formatter = "%Y-%m-%dT%H:%M:%S"
    if timestamp is None:
        timestamp = get_timestamp()
    return datetime.fromtimestamp(timestamp).strftime(formatter)


def get_timestamp():
    return int(time.time())


def remove_duplicate(features, duplicate_score=0.98):
    features = np.array(features)
    sim = cosine_similarity(features, features)

    sim[sim >= duplicate_score] = 1  # is duplicate
    sim[sim < duplicate_score] = 0  # not duplicate
    ids = set()

    for idx in range(sim.shape[0]):
        cluster = np.where(sim[idx] == 1)[0].tolist()  # get duplicate cluster
        ids.add(cluster[0])  # get one if duplicate

    return features[np.array(list(ids))].tolist(), list(ids)
