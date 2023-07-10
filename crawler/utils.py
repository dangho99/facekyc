import json
import time
import requests
from logger import logger
from configparser import ConfigParser
import xmltodict

# Utility
contact_fields = "zfullname, zcfg_requester_comboname, zcfg_requester_address_email, " \
                 "zcfg_requester_id_passport, zcfg_requester_address, zcfg_requester_card_number, " \
                 "zcfg_requester_organization, zcfg_requester_phone_number, zcfg_requester_postion, zapprover"

cr_fields = "category, zfullname, zcfg_requester_comboname, zcfg_requester_address_email, " \
            "zcfg_requester_id_passport, zcfg_requester_address, zcfg_requester_card_number, " \
            "zcfg_requester_organization, zcfg_requester_phone_number, zcfg_requester_postion, " \
            "customer, zcfg_requester_access_purpose, zcustomers_with_contract, zcontractors, " \
            "zvisitor, zother, zpnttp, zcfg_meeting_room, zcfg_tape_room, zcfg_corridor, zcfg_customer_area, " \
            "zfloor_third, zfloor_fourth, zcfg_server_room, zcfg_usp_room, zcfg_noc_room, zcfg_network_room, zNeed_Tiv_support, " \
            "zstart_date, zend_date, ztask"

mapping_cr_fields = "cnt, zcfg_requester_address_email"

# required_fields = ['zfullname',
#                    'zcfg_requester_comboname',
#                    'zcfg_requester_phone_number',
#                    'zcfg_requester_address_email',
#                    'zcfg_requester_id_passport',
#                    'zcfg_requester_postion']


# Call API to get data using method GET
def get_data(url, to_dict=True, **kwargs):
    """
    @params:
        - url: api
        - **kwargs: headers={},
            auth={}, --> auth = (auth["username"], auth["password"])
            params={}
    return:
        - data: is dict
        data = {
            ''
        }
    """
    # Step 1: Check url is valid?
    if url is None:
        logger.info("Please check the url!")
    # Step 2: Get configuration parameters
    config_params = {k: v for k, v in kwargs.items()}

    try:
        # Step 3: Create a request and Perform call to DC Backend through the request
        response = requests.get(
            url=url,
            headers=config_params.get("headers", {}),
            params=config_params.get("params", {})
        )
        # Step 4: Check status
        if not response:
            return

        if response.ok:
            logger.info("Successfully fetched the data")
        else:
            logger.error(f"There's a {response.status_code} error with your request")
            return

        # Step 5: Parse XML to DICT
        if not to_dict:
            return response.text

        response = xmltodict.parse(response.content)
        return response

    except Exception as e:
        logger.debug("Didn't connect to DC Backend caused by ", e)
        return


# Create/Update a resource using method POST
def post_data(url, **kwargs):
    """
    @params:
        - url: api
        - **kwargs: headers={}, auth={}, body={}
    return:
        data = {}
    """
    # Check the url is valid
    # Step 1: url of the api to get access key from DC server
    if url is None:
        logger.info("Please check the url!")
        return
    # Get configuration params
    params = {k: v for k, v in kwargs.items()}
    # Step 2: creating HTTP response object from given url
    try:
        # Perform call api with input includes: url + parameters
        response = requests.post(
            url=url,
            auth=(params["auth"]["username"], params["auth"]["password"]),
            headers=params["headers"],
            data=params["body"]["raw"],
            timeout=3
        )
        # Step 3: checking the status's request
        if response.ok:
            logger.info("Successfully update the data with parameters provided -"
                        " status_code: {}".format(response.status_code))
        else:
            logger.error(f"There's a {response.status_code} error with your request")
            return
        # Step 4: Parse XML to DICT
        response = xmltodict.parse(response.content)

        return response

    except Exception as e:
        logger.debug("Didn't call to api caused by: ".format(e))
        return


def validate_access_key(expiration_time, time_to_live=7 * 24 * 60):
    """
    @params:
        - access_key: which given from (1)
    """
    # expiration_time = key_generation_time + time_to_live
    """
    where:
        - expiration_time: timestamp
        - time_to_live: the default time of access key is valid
    """

    if not expiration_time:
        return False

    if int(time.time()) > int(expiration_time):
        return False

    return True


def check_valid_user(user_data: dict):
    fields = [
        'zcfg_requester_address_email',
        'zcfg_requester_id_passport'
    ]

    is_valid = True
    if not user_data:
        is_valid = False
        return is_valid

    # Replace: Nếu có trường thông tin nhưng không có giá trị thì có đăng ký không?
    # Nếu hệ thống cho update thông tin thì cứ đăng ký. Chỉ cần check có tồn tại key hay không?
    # for field in fields:
    #     if field not in user_data:
    #         is_valid = False
    #         return is_valid

    for field in fields:
        if not user_data.get(field):

            is_valid = False
            return is_valid

    return is_valid


def check_status_user(zend_date):
    """
    @params:
        - zend_date: timestamp() --> int
    return:
        - active: True or False --> boolean
    """
    active = False
    if not zend_date:
        return active

    if int(zend_date) > int(time.time()):
        active = True
        return active

    return active


def config(filename='./system_env/config.ini', cf_section=None):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
    # get section, default to redis
    params = {}
    # if section:
    #     if parser.has_section(section):
    #         params[section] = {}
    #         items = parser.items(section)
    #         for item in items:
    #             params[section][item[0]] = item[1]
    #         return params
    #
    #     else:
    #         raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    for section in parser.sections():
        params[section] = {}
        items = parser.items(section)
        for item in items:
            params[section][item[0]] = item[1]

    if cf_section:
        return params.get(cf_section, "")

    return params


# if __name__ == "__main__":
#     # api_call = MakeApiCall("https://dev.to/api/articles")
#     print(validate_access_key(expiration_time=""))
