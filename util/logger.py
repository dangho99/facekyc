from datetime import datetime
import logging
import time
import sys
import os


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging


def get_timestamp():
    formatter = "%Y-%m-%d %H:%M:%S"
    return datetime.fromtimestamp(time.time()).strftime(formatter)


def get_logger(model_dir, filename="run.log"):
    global logger
    logger = logging.getLogger(os.path.basename(model_dir))
    logger.setLevel(logging.DEBUG)
  
    formatter = logging.Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    h = logging.FileHandler(os.path.join(model_dir, filename))
    h.setLevel(logging.DEBUG)
    h.setFormatter(formatter)
    logger.addHandler(h)
    return logger