## Free Identity verification KYC

Run demo:

```sh
# deploy redis broker
bash broker/redis.sh

# sign up and sign in
python3 upload.py

# face detection and encoding
python3 gateway.py

# trainer or indexing
python3 train.py

# predictor
python3 predict.py
```
