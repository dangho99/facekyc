import time

import redis
from pymongo import MongoClient
from logger import logger
from utils import config

params = config()


def connect_redis():
    conn = None

    while not conn:
        try:
            conn = redis.Redis(
                host=params.get("redis", "").get("host", ""),
                port=params.get("redis", "").get("port", ""),
                db=params.get("redis", "").get("db", ""),
                password=params.get("redis", "").get("password", ""),
            )

            if conn.ping():
                logger.info("Successfully connected to Redis")
            return conn
        except Exception as e:
            logger.debug("Didn't connect to Redis caused by ", e)
            time.sleep(1)

    return


def connect_mongodb():
    "https://www.mongodb.com/languages/python"
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = params.get("mongodb", "").get("url", "")
    client = None

    while not client:
        try:
            # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
            client = MongoClient(CONNECTION_STRING)
            logger.info("Successfully connected to MongoDB")

            return client

        except Exception as e:
            logger.debug("Didn't connect to MongoDB caused by ", e)
            time.sleep(1)

    return


