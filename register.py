from pathlib import Path
import requests
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
    url = "https://127.0.0.1:8999/api/user/pattern"
    data_dir = "data"

    for user_dir in os.listdir(data_dir):
        user_dir = os.path.join(data_dir, user_dir)
        if not os.path.isdir(user_dir):
            continue
        with open(os.path.join(data_dir, os.path.basename(user_dir)+'.json'), "w") as f:
            images = []
            for img_file in os.listdir(user_dir):
                img_path = os.path.join(user_dir, img_file)
                img_byte = dataio.convert_img_to_bytes(img_path)
                images.append(img_byte)
            payload = {
                "images": images,
                "zcfg_requester_comboname": os.path.basename(user_dir),
                "zcfg_requester_address_email": "{}@gmail.com".format(os.path.basename(user_dir)),
                "zcfg_requester_id_passport": fake()[:9],
                "zcfg_requester_phone_number": fake(),
                "zcfg_requester_access_purpose": "tour",
                "attachments": "",
                "zcfg_approver_comboname": "administrator",
                "zcfg_approver_address_email": "superadmin@telehouse.com",
                "zusing": True,
                "zstart_date": "2022-09-01 08:00:00",
                "zend_date": "2022-09-01 10:00:00",
            }
            r = requests.post(url=url, json=payload)
            print(user_dir, r.json())
            json.dump(payload, f, indent=2)


if __name__ == "__main__":
    random.seed(1234)
    gen()
