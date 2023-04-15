from PIL import Image
import numpy as np
import requests
import base64
import random
import json
import os
import io


def generate():
    url = "https://192.168.0.2:8999/api/user/pattern"
    data_dir = "data"

    for user_dir in os.listdir(data_dir):
        user_dir = os.path.join(data_dir, user_dir)
        if not os.path.isdir(user_dir):
            continue
        with open(os.path.join(data_dir, "{}.json".format(os.path.basename(user_dir))), "w") as f:
            images = []
            for img_file in os.listdir(user_dir):
                img_path = os.path.join(user_dir, img_file)
                img_byte = convert_img_to_bytes(img_path)
                images.append(img_byte)
            payload = {
                "images": images,
                "zcfg_requester_comboname": os.path.basename(user_dir),
                "zcfg_requester_address_email": "{}@gmail.com".format(os.path.basename(user_dir)),
                "zcfg_requester_id_passport": random.randint(000000000000, 999999999999),
                "zcfg_requester_phone_number": random.randint(0000000000, 9999999999),
                "active": True,
                # "zcfg_requester_access_purpose": "tour",
                # "attachments": "",
                # "zcfg_approver_comboname": "administrator",
                # "zcfg_approver_address_email": "superadmin@telehouse.com",
                # "zusing": True,
                # "zstart_date": "2022-09-01 08:00:00",
                # "zend_date": "2022-09-01 10:00:00",
            }
            r = requests.post(url=url, json=payload, verify=False)
            print(user_dir, r.json())
            json.dump(payload, f, indent=2)


def convert_img_to_numpy_array(img_path, new_width=500):
    # TODO: load image from directory and convert to numpy array
    img = Image.open(img_path)
    img.convert("RGB").save(img_path, "JPEG")
    img = Image.open(img_path)

    # resize with aspect ratio
    if max([img.height, img.width]) > new_width:
        aspect_ratio = img.height / img.width
        new_height = new_width * aspect_ratio
        img = img.resize((int(new_width), int(new_height)))

    # convert to array
    array = np.asarray(img)
    print(array.shape)
    return array


def convert_numpy_array_to_bytes(array: np.array) -> str:
    # TODO: convert numpy array to bytes
    compressed_file = io.BytesIO()
    Image.fromarray(array).save(compressed_file, format="JPEG")
    compressed_file.seek(0)
    return base64.b64encode(compressed_file.read()).decode()


def convert_img_to_bytes(img_path):
    # TODO: convert img to bytes
    array = convert_img_to_numpy_array(img_path)
    return convert_numpy_array_to_bytes(array)


def convert_bytes_to_numpy_array(j_dumps: str) -> np.array:
    # TODO: load json string to numpy array
    compressed_data = base64.b64decode(j_dumps)
    img = Image.open(io.BytesIO(compressed_data))
    return np.array(img)


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    random.seed(1234)
    generate()
