## Free Identity verification KYC

```sh
# Deploy MongoDB and Redis queue
docker-compose up -d

# Deploy face recognition model
python3 gateway.py

# Deploy indexing model 
python3 server.py

# Deploy backend api
python3 main.py
```
