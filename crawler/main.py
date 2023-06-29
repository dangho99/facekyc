from utils import config
from sync_data import execute
from connection import connect_redis

# params = config()
# redis_conn = connect_redis()
# Refactor: Singletone

if __name__ == "__main__":
    execute()
