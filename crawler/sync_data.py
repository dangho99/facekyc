import os
import json
import time
import redis
import requests
import pandas as pd

from tqdm import tqdm
from logger import logger
from datetime import datetime
from connection import connect_redis
from utils import get_data, post_data
from utils import contact_fields, cr_fields
from utils import config, check_valid_user, validate_access_key


requests.packages.urllib3.disable_warnings()


# 1. Call API to DC Backend to get the access key data
def get_access_key(url=None, **kwargs):
    """
    @params:
        - url: is the api which interacting with DC Server - return access key
        - method: post
    return:
        - access_key: key authentication
    """
    # Perform call api to DC Backend

    if url is None:
        url = "https://telehouse.hypersd.vn:8050/caisd-rest/rest_access"

    response = post_data(url=url, **kwargs)
    # Return the value's of access key
    data = {
        "access_key": response.get("rest_access", "").get("access_key", ""),
        "expiration_date": response.get("rest_access", "").get("expiration_date", "")
    }

    return data.get("access_key"), data.get("expiration_date")


# 2. Call API to contact url in the DC Backend: Get the information data of users
def get_contact_data(url=None, **kwargs):
    # fields = contact_fields.split(", ")
    required_fields = [
        'zfullname',
        'zcfg_requester_comboname',
        'zcfg_requester_phone_number',
        'zcfg_requester_address_email',
        'zcfg_requester_id_passport',
        'zcfg_requester_position'
    ]

    """
    @params:
        - access_key: given from the result of get_access_key function
        - fields: are the field information of user
    return: the contact data of users
    contact_data = [
        {
            "id": <@id>
            "zfullname": <str>,
            ...
        },
        ...
        {}
    ]
    Note: contact_data = [{}, ..., {}} is a list of dict where an item represents for a user correspondingly
    """
    contact_data = []
    # Perform call api(method: get) to DC Backen to get contact data
    if url is None:
        url = "https://telehouse.hypersd.vn:8050/caisd-rest/cnt"

    response = get_data(url=url, **kwargs)

    if not response:
        return

    if not response.get("collection_cnt", "").get("cnt", ""):
        return

    for item in response.get("collection_cnt").get("cnt"):
        user_data = {"id": item.get('@id', "")}

        for field in required_fields:
            user_data[field] = item.get(field, "")

        # Adds: Default the status of user is True: if the user is staff, active is True and vice versa
        if user_data.get("zcfg_requester_address_email").endswith("@telehouse.vn"):
            user_data["active"] = True
        else:
            user_data["active"] = False

        # Assign the value of field: zfullname
        if (user_data.get("zfullname", "") is None) and (user_data.get("zcfg_requester_comboname", "") is not None):
            user_data["zfullname"] = user_data["zcfg_requester_comboname"]

        contact_data.append(user_data)

    return contact_data


# 3. GET CR: Customer register data
def get_cr_data(url=None, **kwargs):
    """
    @param:
        - url: "https://telehouse.hypersd.vn:8050/caisd-rest/cr?WC=category%3D'pcat:400491'&size=10000"
        - **kwargs: the optional params
    return:
        - cr_data: the data of customer which registering to DC
        cr_data = [
            {},
            
        ]
    """
    requrired_fields = [
        'zfullname',
        'zcfg_requester_comboname',
        'zcfg_requester_organization',
        'zcfg_requester_phone_number',
        'zcfg_requester_address_email',
        'zcfg_requester_id_passport',
        'zcfg_requester_position',
        'zstart_date',
        'zend_date',
        'ztask'
    ]
    # Requried_fields include a field: id which adds in following.

    cr_data = []
    # Perform call api(method: get) to DC Backen to get contact data
    if url is None:
        url = "https://telehouse.hypersd.vn:8050/caisd-rest/cr?WC=category%3D'pcat:400491'&size=10000"

    response = get_data(url=url, **kwargs)
    if not response:
        return

    if not response.get("collection_cr", "").get("cr", ""):
        return

    # Aggregate data
    for item in response.get("collection_cr").get("cr"):
        """
        cr_item = {
            "cr_id": "<str>",
            "user_id: <str>,
            'zfullname': <str>,
            'zcfg_requester_comboname': <str>,
            'zcfg_requester_organization': <str>,
            'zcfg_requester_phone_number': <str>,
            'zcfg_requester_address_email': <str>,
            'zcfg_requester_id_passport': <str>,
            'zcfg_requester_position': <str>,
            'zstart_date': <str>,
            'zend_date': <str>,
            'ztask': <str>
            'active': <bool>
        }
        """

        cr_item = {"cr_id": item.get("@id", ""), "user_id": item.get("customer", "").get("@id", "")}

        for field in requrired_fields:
            cr_item[field] = item.get(field, "")

        # Assign the value of field: zfullname by zcfg_requester_comboname
        if (cr_item.get("zcfg_requester_comboname") is not None) and (cr_item.get("zfullname") is None):
            cr_item["zfullname"] = cr_item["zcfg_requester_comboname"]

        # Get the status of active of user
        if cr_item.get("zcfg_requester_address_email").endswith("@telehouse.vn"):
            cr_item["active"] = True
        elif not cr_item.get("zend_date"):
            cr_item["active"] = False
        elif int(cr_item.get("zend_date")) >= int(time.time()):
            cr_item["active"] = True
        else:
            cr_item["active"] = False

        cr_data.append(cr_item)

    return cr_data


# 4. GET mapping between CNT vs CR
def get_mapping_cnt_to_cr(url=None, **kwargs):
    """
    @params:
        - url: api
        - **kwargs: params
    return:
        - map_cnt_cr: list
    """
    map_cnt_cr = []
    if url is None:
        url = "https://telehouse.hypersd.vn:8050/caisd-rest/zlrel_cr_cnt/?WC=cr='cr:{id_cr}'"

    return map_cnt_cr


# 5. GET Image Attachment CNT
def get_id_file(user_id, url=None, **kwargs):
    """
    @params:
        - user_id: is the id which given from the get_contact_data()
    return:
        - id_file_data is a dict:
    id_file_data = {
        "id": str<user_id>,
        "zattmnt": [str<zattmnt-id_1>, str<zattmnt-id_2>, str<zattmnt-id_3>]
    }
    """

    if url is None:
        url = "https://telehouse.hypersd.vn:8050/caisd-rest/zlrel_cnt_attmnt"
    # Create a request to get id_file(zattmnt_id) - is the filename 's image
    response = get_data(url=url, **kwargs)

    # Processing the response to get data updating to id_file_data
    if not response:
        return

    id_file_data = {"id": user_id, "zattmnt": []}

    zattmnt_list = response.get("collection_zlrel_cnt_attmnt").get('zlrel_cnt_attmnt')
    if not zattmnt_list:
        return

    for item in zattmnt_list:
        zattmnt_id = item.get("zattmnt").get("@id")
        id_file_data["zattmnt"].append(zattmnt_id)

    return id_file_data


# 6. GET Image data
def get_image_data(id_file, url=None, **kwargs):
    """
    @params:
        - id_file: is a zattmnt - identification file
    return:
        - image_data: a dict
    image_data = {
        "id": str<user_id>,
        "images": {
            "str<zattmnt-id_1>": str<base64>,
            ...
        }
    }
    """
    image_data = None
    """Adds: Processing func"""

    if url is None:
        url = f"https://telehouse.hypersd.vn:8050/caisd-rest/attmnt/{id_file}/file-resource"
    else:
        url = url.format(id_file=id_file)

    # Create a request to get data from DC Backend

    response = get_data(url=url, to_dict=False, **kwargs)
    if not response:
        return

    # Check the key in response to get image data (base64) -- !!!
    if isinstance(response, str):
        image_data = response.replace('"','').replace('\r\n','')
        image_data = image_data.split(',')[-1]

    return image_data


# 7. Send data which includes the required information to redis
def send_data_to_redis(redis_conn, data, params):
    """
    Producer: LPUSH and Consumer: RPOP ==> Strategy: First IN, First Out (FIFO)
    @params:
        data: is a dict
    return:
        message
    """
    try:
        redis_conn.lpush(params.get("redis", "").get("sync_queue"), data)
        return {"status_code": 200, "message": "Sent the data to Redis successfully!"}

    except Exception as e:
        return {"status_code": 500, "message": "Didn't send data to Redis caused by: {}".format(e)}


# 8. Perform call to API:"https://localhost:8999/api/user/pattern" to register the user
def register(url="https://localhost:8999/api/user/pattern", payload=None):
    if payload is None:
        payload = {}

    try:
        resp = requests.post(url=url, json=payload, verify=False)
        return resp.json()
    except Exception as e:
        logger.debug("Didn't register the user caused by: ", e)
        return {"status_code": 500, "message": "Didn't register the user to Kotora Sever caused by: {}".format(e)}


def execute(window_time=3600):
    """
    @params:
        - window_time: After window_time (seconds) perform the synchronization progress - default: 3600 (s)
    """
    logger.info("STARTING SYNCHOR")
    # Read configuration parameters
    params = config()
    # Update the value of window_time param
    window_time = int(params.get("system").get("window_time"))

    # Initialize connection to redis server
    # redis_conn = connect_redis()

    # 1: Get access key and expiration date
    logger.info("GET ACCESS KEY FROM DC BACKEND...")
    access_key, expiration_date = get_access_key(
        url=params.get("data_center").get("access_key_url"),
        auth={"username": params.get("data_center").get("username"),
              "password": params.get("data_center").get("password")},
        headers={'Content-Type': 'application/xml'},
        body={"mode": "raw", "raw": "<rest_access/>"}
    )
    logger.info("SUCCESSFULLY THE GIVEN ACCESS KEY!")
    while True:
        """
        PROCESS FLOW
        """
        start_time = time.time()

        # 2: Check the expiration date of access key
        logger.info("VERIFY THE ACCESS KEY IS VALID...")
        is_valid = validate_access_key(expiration_time=expiration_date)
        if not is_valid:
            access_key, expiration_date = get_access_key(
                url=params.get("data_center").get("access_key_url"),
                auth={"username": params.get("data_center").get("username"),
                      "password": params.get("data_center").get("password")},
                headers={'Content-Type': 'application/xml'},
                body={"mode": "raw", "raw": "<rest_access/>"}
            )

        """SYNC DATA FOR: CUSTOMER REGISTER (CR)"""
        # 3: GET CR
        cr_data = get_cr_data(
            url=params.get("data_center").get("cr_data_url", ""),
            headers={
                "X-AccessKey": access_key,
                "X-Obj-Attrs": cr_fields
            },
            params={
                "WC": "category='pcat:400491'",
                "size": "10000"
            }
        )
        # Process cr_data => Determine the status of customer
        cr_df = pd.DataFrame(cr_data)
        active_cr_data = cr_df.groupby("user_id").apply(lambda sub_df: any(sub_df["active"].values.tolist())).to_dict()
        # active_cr_data = {
        #   "<user_id>": <active>       # active is True or False
        # }

        # 4: GET MAPPING CNT TO CR --> DON'T USE !
        """SYNC DATA FOR: CONTACT"""
        logger.info("STARTING GET CONTACT DATA FROM DC BACKEND...")
        # 5: GET the contact data from DC Sever
        contact_data = get_contact_data(
            url=params.get("data_center").get("cnt_data_url", ""),
            headers={
                "X-AccessKey": access_key,
                "X-Obj-Attrs": contact_fields
            },
            params={
                "WC": "delete_flag='0'",
                "size": "10000"
            }
        )
        if not contact_data:
            time.sleep(window_time)
            continue

        logger.info("SUCCESSFULLY THE GIVEN CONTACT DATA!")
        # 6: GET the id file which is name of image
        logger.info("STARTING GET THE ID FILE IMAGE AND IMAGE DATA OF USERS")
        for user_data in contact_data:
            # Create a new dict of each user to avoid storage all data in contact_data
            """
            user_data = {
                "id": <user_id>,
                "zfullname": <str>,
                ...,
                "zattmnt": [],
                "images": []
            }
            """
            # Perform create request to get id file according to user_id
            id = user_data.get("id")
            id_file_data = get_id_file(
                url=params.get("data_center").get("id_file_url", ""),
                user_id=id,
                headers={"X-AccessKey": access_key, "X-Obj-Attrs": "zattmnt"},
                params={
                    "WC": "zcnt={}".format(id)
                }
            )
            if not id_file_data:
                continue

            zattmnts = id_file_data.get("zattmnt", "")
            if not zattmnts:
                continue

            # Update a new key-value to user-data
            user_data["zattmnt"] = zattmnts

            # Declare a new key-value to store the image data
            user_data["images"] = []
            # 7: GET image data
            for zattmnt in zattmnts:
                image = get_image_data(
                    id_file=zattmnt,
                    url=params.get("data_center").get("image_data_url", ""),
                    headers={"X-AccessKey": access_key}
                )
                if not image:
                    continue
                user_data["images"].append(image)

            """ADDS MECHANISM TO DETERMINE STATUS OF USER_DATA (ACTIVE) THROUGH (START_DATE & END_DATE)"""
            if id in active_cr_data:
                user_data["active"] = any([user_data["active"], active_cr_data[id]])

            # Check the user data includes the required information
            is_valid_user = check_valid_user(user_data)
            if not is_valid_user:
                continue

            # Don't send the user data to redis => Replace by call to the api: register
            # 8.1: Sent data to redis
            # logger.info("SEND THE USER DATA TO REDIS...")
            # resp = send_data_to_redis(redis_conn=redis_conn, data=user_data)
            # logger.info(resp.get("message"))

            # 8.2: Register the user by calling api register in BE
            # Adds: Call to api: register
            logger.info("Registering the user to BE...")
            resp = register(url=params["system"]["register_api"], payload=user_data)
            logger.info(json.dumps(resp))

        processed_time = time.time() - start_time
        logger.info("THE PROCESSED TIME: {}".format(processed_time))
        logger.info("SUCCESSFULLY DATA SYNCHRONIZATION FROM DC TO KTR!")

        time.sleep(window_time)

    return


if __name__ == "__main__":
    print("HBLCorp!")
    execute()
