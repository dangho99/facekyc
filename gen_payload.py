from pathlib import Path
import random
import json
import os

from util import dataio


def fake():
    prefix = [
        '096','097','098','032','033','034','035','036','037','038','039'
        ]
    start = random.choice(prefix)
    end = random.randint(0000000, 9999999)
    return start + str(end)


def gen():
    with open("payload.json", "w") as f:
        f.write("")

    data_dir = "data"
    for img_path in Path(data_dir).glob("**/*.jpg"):
        img_path = str(img_path)
        if "test" in img_path:
            # verify payload format
            payload = {
                "images": [dataio.convert_img_to_bytes(img_path)]
            }
        else:
            # register payload format

            payload = {
                "images": [dataio.convert_img_to_bytes(img_path)],
                "zcfg_requester_address_email": "{}@gmail.com".format(os.path.basename(img_path)),
                "zcfg_requester_id_passport": fake()[:9],
                "zcfg_requester_phone_number": fake()
            }
        with open("payload.json", "a") as f:
            f.write(json.dumps(payload)+"\n")


if __name__ == "__main__":
    random.seed(1234)
    gen()