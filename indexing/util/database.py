import pymongo
import os


db_uri = "mongodb://{}:{}@{}:{}/".format(
    os.getenv("MONGO_USER", "admin"),
    os.getenv("MONGO_PASSWORD", "P4ssW0rD"),
    os.getenv("API_HOST", "127.0.0.1"),
    os.getenv("MONGO_PORT", "27017")
)


def connect_db(collection_name: str):
    """
    Connect to specific collection
    """
    client = pymongo.MongoClient(db_uri)
    db = client["kotora"]
    return db[collection_name]


def close_db():
    """
    Close the connection to database
    """
    client = pymongo.MongoClient(db_uri)
    client.close()
    return
