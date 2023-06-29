import requests
import xmltodict
from utils import get_data


def get_access_key(url=None, **kwargs):
    # **kwargs: key-value arguments
    if url is None:
        url = "https://telehouse.hypersd.vn:8050/caisd-rest/rest_access"
    # 1. Get configuration parameters
    params = {k: v for k, v in kwargs.items()}
    params["url"] = url
    print(params)
    print(params["body"]["raw"])

    # 2. Create a request
    response = None
    try:
        response = requests.post(
            url=params["url"],
            auth=(params["auth"]["username"], params["auth"]["password"]),
            headers=params["headers"],
            data=params["body"]["raw"]
        )
        print("response")
        print(response.content)
        print("Convert xml to dict")
        print(xmltodict.parse(response.content))
        print("Status code: ", response.status_code)
        print(response.url, response.request, response.headers)

    except Exception as e:
        print(e)

    # 3.
    return


# # 1. Get access key using method post
headers = {'Content-Type': 'application/xml'}
resp = get_access_key(auth={"username": "telehouse", "password": "Tiv@2021#$"},
               headers={'Content-Type': 'application/xml'},
               body={"mode": "raw", "raw": "<rest_access/>"})


# # 2. Get the information data of contact
# get_data(
#     url="https://telehouse.hypersd.vn:8050/caisd-rest/cnt",
#     headers={
#         "X-AccessKey": "39884355",
#         "X-Obj-Attrs": "zfullname, zcfg_requester_address_email"
#     },
#     params={
#         "WC": "delete_flag='0'",
#         "size": 10000
#     }
# )
# ## Test 2: Get information data
# from sync_data import get_contact_data
# from utils import contact_fields
#
# response = get_contact_data(
#             headers={
#                 "X-AccessKey": "39884355",
#                 "X-Obj-Attrs": contact_fields
#             },
#             params={
#                 "WC": "delete_flag='0'",
#                 "size": "10000"
#             }
#         )
#
# print(response)

# # 3. Get the id file - is the name of image corresponding to each user
# response = get_data(
#     url="https://telehouse.hypersd.vn:8050/caisd-rest/zlrel_cnt_attmnt",
#     headers={"X-AccessKey": "39884355", "X-Obj-Attrs": "zattmnt"},
#     params={
#         "WC": "zcnt=U'6D8AA2E81E358843A8D3FF647AEE38F6'"
#     }
# )
# print(response.url)
# print(response)
# exit()
# print(response.get(""))
# test_3
# from sync_data import get_id_file
# id = "U'6D8AA2E81E358843A8D3FF647AEE38F6'"
# id_file_data = get_id_file(
#                 user_id=id,
#                 headers={"X-AccessKey": "39884355", "X-Obj-Attrs": "zattmnt"},
#                 params={
#                     "WC": "zcnt={}".format(id)
#                 }
#             )
# print(id_file_data)

# # 4. Test get_image_file
# from sync_data import get_image_data
# zattmnt = "404612"
# access_key = "39884355"
# image = get_image_data(id_file=zattmnt, headers={"X-AccessKey": access_key})
# print(image)

"""TEST API: GET CR"""
from sync_data import get_cr_data
from utils import cr_fields
# get_cr_data(
#     headers={
#         "X-AccessKey": "430998362",
#         "X-Obj-Attrs": cr_fields
#         },
#     params={
#         "WC": "category%3D'pcat:400491'",
#         "size": "10000"
#     }
# )
"""TEST API: GET MAPPING CNT INTO CR"""


response = get_cr_data(
            url="https://telehouse.hypersd.vn:8050/caisd-rest/cr",
            headers={
                "X-AccessKey": "535364906",
                "X-Obj-Attrs": cr_fields
            },
            params={
                "WC": "category='pcat:400491'",
                "size": 10000
            }
        )

print(response)

from sync_data import get_access_key
access_key, expiration_date = get_access_key(
        auth={"username": "telehouse", "password": "Tiv@2021#$"},
        headers={'Content-Type': 'application/xml'},
        body={"mode": "raw", "raw": "<rest_access/>"}
    )
print(access_key)