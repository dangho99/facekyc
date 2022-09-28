import pymongo
from keeper.environments import SystemEnv


db_uri = "mongodb://{}:{}@{}:27017/".format(SystemEnv.admin_user,
                                            SystemEnv.admin_password,
                                            SystemEnv.host)


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
