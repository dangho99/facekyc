import requests
import numpy as np
import json
import sys

np.random.seed(1234)

url = 'http://localhost:9501/v1/models/face_recognition/versions/{}:predict'.format(sys.argv[1])
fake_data = np.random.rand(5, 160, 160, 3)
print(fake_data.shape)

data = {"instances": fake_data.tolist()}
data = json.dumps(data)
r = requests.post(url, data=data)
#print(r.text)

res = json.loads(r.text)
pred = res["predictions"]
pred = np.array(pred)
print(type(pred))
print(pred.shape)
