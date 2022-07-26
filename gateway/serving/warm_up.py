import tensorflow as tf
from tensorflow_serving.apis import classification_pb2
from tensorflow_serving.apis import inference_pb2
from tensorflow_serving.apis import model_pb2
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_log_pb2
from tensorflow_serving.apis import regression_pb2

import requests
import numpy as np
import json
import sys
import os

inputs = np.random.rand(10, 160, 160, 3)

version = 1
model_dir = "./face_recognition/{}".format(version)
warm_up_dir = os.path.join(model_dir, "assets.extra")
if not os.path.exists(warm_up_dir):
    os.makedirs(warm_up_dir)

with tf.io.TFRecordWriter(os.path.join(warm_up_dir, "tf_serving_warmup_requests")) as writer:
    request = predict_pb2.PredictRequest(
        model_spec=model_pb2.ModelSpec(name="face_recognition"),
        inputs={"inputs": tf.make_tensor_proto(inputs, shape=inputs.shape, dtype=np.float32)}
        )
    log = prediction_log_pb2.PredictionLog(
        predict_log=prediction_log_pb2.PredictLog(request=request))
    for _ in range(10):
        writer.write(log.SerializeToString())
