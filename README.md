## Free Identity verification KYC

docker image: https://drive.google.com/drive/folders/1ILoAqN3V9-_IVMFvyNAcQ_U-2EVEpsIK?usp=sharing

1. Run application (python>=3.8):
```sh
# Deploy MongoDB and Redis queue
docker-compose up -d

# install package
pip3 install -r requirements.txt

# Deploy face recognition model
python3 gateway.py

# Deploy backend api
python3 main.py
```

2. Run API:
- Register (4.1):

`Endpoint`: http://localhost:8999/api/user/pattern

`Method`: POST

`Content-Type`: application/json

`Body`:
```json
{
    "images": ["<image_1>", "<image_2>", "<image_3>", "<image_4>", "<image_5>"],
    "zcfg_requester_comboname": "<requester_fullname>",
    "zcfg_requester_organization": "<organization>",
    "zcfg_requester_address_email": "<requester_email>",
    "zcfg_requester_id_passport": "<cccd/cmnd>",
    "zcfg_requester_phone_number": "<phone_number>",
    "zcfg_requester_access_purpose": "<access_purpose>",
    "attachments": "<upload_files>",
    "zcfg_approver_comboname": "<approver_fullname>",
    "zcfg_approver_address_email": "<approver_email>",
    "zusing": true,
    "znot_using": false,
    "zstart_date": "<checkin_time>",
    "zend_date": "<checkout_time>",
    "ztask": "<task_name>"
}
```

`Response`:
```json
{
    "message": "<message>"
}
```

`Examples`:

- Register without images:
```json
{
    "images": [],
    "zcfg_requester_comboname": "hoang",
    "zcfg_requester_organization": "kotora",
    "zcfg_requester_address_email": "hoang@gmail.com",
    "zcfg_requester_id_passport": "038585963",
    "zcfg_requester_phone_number": "0391408249",
    "zcfg_requester_access_purpose": "tour",
    "attachments": "",
    "zcfg_approver_comboname": "administrator",
    "zcfg_approver_address_email": "superadmin@telehouse.com",
    "zusing": true,
    "zstart_date": "2022-09-01 08:00:00",
    "zend_date": "2022-09-01 10:00:00",
    "ztask": "tour"
}
```
```json
{
    "message": "Register success, but empty images"
}
```

- Register without `zcfg_requester_id_passport` or `zcfg_requester_address_email`:
```json
{
    "images": [],
    "zcfg_requester_comboname": "hoang",
    "zcfg_requester_organization": "kotora",
    "zcfg_requester_phone_number": "0391408249",
    "zcfg_requester_access_purpose": "tour",
    "attachments": "",
    "zcfg_approver_comboname": "administrator",
    "zcfg_approver_address_email": "superadmin@telehouse.com",
    "zusing": true,
    "zstart_date": "2022-09-01 08:00:00",
    "zend_date": "2022-09-01 10:00:00",
    "ztask": "tour"
}
```
```json
{
    "message": "Invalid format, address_email or id_passport not found"
}
```
Because the application will generate the `user_id` according to the formula: `hash_md5(<cccd/cmnd>+"_"+<email>)`  

- Update images for user:
```json
{
    "images": [
        "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
