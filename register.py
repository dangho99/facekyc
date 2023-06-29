from PIL import Image
import numpy as np
import requests
import base64
import random
import json
import os
import io
import pandas as pd


"""
Hướng dẫn sử dụng:
1. Vào link datasheet (google drive) chứa thông tin của KH Telehouse, thực hiện tải file thông tin được lưu dưới định dạng là .csv
2. Thay đổi tên của file chứa thông tin thành: telehouse_conctact.csv
3. Copy file: tehehouse đến thư mục chứa file: register.py
4. Sửa backend ip trong biến api_host ở dòng 24.
5. Thực hiện chạy script: python3 register.py
6. Trường hợp muốn đăng ký lại cho user nào thì phải xóa user đó trong file: registered_users.txt, sau đó chạy lại script như bước 4
"""
customer_info = [
  "Họ và tên", "Tên công ty", "Email", "CCCD", "Số điện thoại", "Lý do truy cập", "Ảnh"
]
#api_host = "10.20.3.190"
api_host = "127.0.0.1"


def read_file(file_path):
    # Load the list of users includes: register or unregister
    f = open(file_path, 'r')
    data = json.load(f)
    return data


def get_registered_users(file_path):
    registered_users = []
    with open(file_path, "r") as f:
        for user in f:
            user = user.strip()
            if not user:
                continue
            registered_users.append(user)
    return registered_users


def write_file(file_path, user):
    with open(file_path, "a") as outfile:
        outfile.write(user + "\n")


def read_contact_data(file_path= './telehouse_contact.csv'):

    if not os.path.exists(file_path):
        return
    # read data => dataframe
    df = pd.read_csv(file_path) 
    # filter data based on customer info
    df = df[customer_info]
    # drop na values
    df.dropna(axis=0, inplace=True)
    df["user_id"] =  df["Email"].apply(lambda x: x.split('@')[0])
    df.set_index('user_id', inplace=True)

    # Convert dataframe to json using format: index
    data = df.to_dict("index")
    # Transform user_id key to lowercase characters
    data = {k.lower(): v for k, v in data.items()}
    print(data.keys())
    print(len(data.keys()))
    return data


def generate():
    # Declare URL - BE Server
    url = "https://{}:8999/api/user/pattern".format(api_host)
    
    # Read the telehouse contact data from csv file which downloaded from Google Driver
    telehouse_contact_data = read_contact_data()

    # Declare data_dir: which contains the image of custormer
    # data_dir = "/home/kotora/Workspace/DC4/deploy/new-data/eKYC"
    data_dir = "./data"
    users = [user_dir for user_dir in os.listdir(data_dir) if not user_dir.endswith(".json")]
    print("List of Users \n", users)
    print(len(users))

    # Initialize registered_users
    registered_users = []
    if os.path.exists("./registered_users.txt"):
        registered_users = get_registered_users(file_path="./registered_users.txt")
    print("List of the registered users: \n", registered_users)
    
    count = 0
    for user_dir in users:
        print("User directory: ", user_dir)
        if user_dir in registered_users:
            continue
        print("Perform Register for ", user_dir)
        
        # Assign user_dir to user_id before user_dir which re-assign
        user_id = user_dir  
        # Get the information of user_id from telehouse_contacta_data by user_id
        if not user_id.lower() in telehouse_contact_data:
            print("Invalid!!!")
            write_file(file_path="./registered_users.txt", user=user_id)
            break
        info_data = telehouse_contact_data.get(user_id.lower())

        user_dir = os.path.join(data_dir, user_dir)
        if not os.path.isdir(user_dir):
            continue

        with open(os.path.join(data_dir, "{}.json".format(os.path.basename(user_dir))), "w") as f:
            images = []
            for img_file in os.listdir(user_dir):
                img_path = os.path.join(user_dir, img_file)
                img_byte = convert_img_to_bytes(img_path)
                images.append(img_byte)
            print("The number of images of user are: ", len(images))

            payload = {
                "images": images,
                "zcfg_requester_comboname": user_id,
                "zcfg_requester_address_email": info_data.get("Email", ""),
                "zcfg_requester_id_passport": info_data.get("CCCD", ""),
                "zcfg_requester_phone_number": info_data.get("Số điện thoại", ""),
                "zfullname": info_data.get("Họ và tên"),  # added by lochb
                "zcfg_requester_position": info_data.get("Lý do truy cập"), # added by lochh
                "active": True,
                # "zcfg_requester_access_purpose": "tour",
                # "attachments": "",
                # "zcfg_approver_comboname": "administrator",
                # "zcfg_approver_address_email": "superadmin@telehouse.com",
                # "zusing": True,
                # "zstart_date": "2022-09-01 08:00:00",
                # "zend_date": "2022-09-01 10:00:00",
            }
            # print(payload)
            for k, v in payload.items():
                if k != "images":
                    print(k, v)
            
            # Perform send a request to BE server
            r = requests.post(url=url, json=payload, verify=False)
            print(user_dir, r.json())
            json.dump(payload, f, indent=2)

            count += len(images)
            print("The total of images which processed are: ", count)
        
        write_file(file_path="./registered_users.txt", user=user_id)
        break

    print("Number of images which registered are: ", count)

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


def delete():
    url = "https://{}:8999/api/user/pattern".format(api_host)

    payload = {
        "zcfg_requester_address_email": "pham_hoang@gmail.com",
        "zcfg_requester_id_passport": 858849378233,
    }
    r = requests.delete(url=url, json=payload, verify=False)
    print(r.json())


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    random.seed(1234)
    generate()
