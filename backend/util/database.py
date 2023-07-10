import pymongo
import os


db_uri = "mongodb://{}:{}@{}:{}/".format(
    os.getenv("MONGO_USER", "admin"),
    os.getenv("MONGO_PASSWORD", "P4ssW0rD"),
    os.getenv("MONGO_HOST", "127.0.0.1"),
    os.getenv("MONGO_PORT", "27017")
)


def connect_db():
    """
    Connect to specific collection
    """
    client = pymongo.MongoClient(db_uri)
    db = client["kotora"]
    return db


def close_db():
    """
    Close the connection to database
    """
    client = pymongo.MongoClient(db_uri)
    client.close()
    return


def get_latest_db(collection, field):
    res = list(collection.find(
            {}, {field: 1, '_id': 0}
        ).sort(
            [(field, -1)]
        ).limit(
            1
        )
    )

    if not len(res):
        return os.getenv("MODEL_INIT", "0")

    return res[0][field]
