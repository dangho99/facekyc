
# Hướng dẫn cài đặt backend KYC local

## 1. Requirements
- OS: Ubuntu 18.04, 20.04
- CPU: 4 Cores
- RAM: 8GB
- SSD: 128GB

## 2. Cài đặt các package cần thiết
### 2.1. Docker

Cập nhật `apt` package:
```sh
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release
```

Thêm docker GPG key vào `apt`:
```sh
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

Add docker repo:
```sh
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Cài đặt docker:
```sh
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

Test: 
```sh
docker -v
```
Thấy hiện phiên bản docker là thành công:

![](images/docker-version.png)

### 2.2 Docker Compose
Tải docker-compose binary file:
```sh
wget https://github.com/docker/compose/releases/download/v2.4.1/docker-compose-linux-x86_64
```

Tạo symbolic link để chạy docker-compose command:
```
mv docker-compose-linux-x86_64 /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose --force
```

Test:
```sh
docker-compose -v
```
Thấy hiện phiên bản docker-compose là thành công:

![](images/docker-compose-version.png)

## 3. Triển khai backend

### 3.1. Clone code từ github
```sh
git clone https://github.com/hoangph3/face-kyc-api
```

### 3.2. Build và run container from source

Chỉnh sửa file cấu hình `env.json`:

```json
{
  "host": "localhost",
  "k": 5,
  "n_dims": 512,
  "duplicate_score": 0.99,
  "distance_metric": "cosine",
  "checkpoint_path": "ckpt/v0.0.1",
  "serving_host": "http://localhost:8501/api/user/pattern",
  "admin_user": "admin",
  "admin_password": "P4ssW0rD"
}
```

Sửa trường `host` và `serving_host`, trong đó `host` là ip local của hệ thống, `serving_host` và ip của hệ thống AI Box, sử dụng editor `nano`:

Sau khi sửa thành công:
```json
{
  "host": "172.16.36.43",
  "k": 5,
  "n_dims": 512,
  "duplicate_score": 0.99,
  "distance_metric": "cosine",
  "checkpoint_path": "ckpt/v0.0.1",
  "serving_host": "http://172.16.36.43:8501/api/user/pattern",
  "admin_user": "admin",
  "admin_password": "P4ssW0rD"
}
```
Ở đây giả sử  backend và AI Box cùng deploy trên cùng một server với ip local: `172.16.36.43`.

Chạy lệnh sau để deploy:

```sh
docker-compose up -d --build
```

Cấu hình được define như sau (xem trong file `docker-compose.yml`):
- mongo database chạy ở port `27017` với credential `admin:P4ssW0rD`.
- mongo express chạy ở port `8081` với credential tương tự như mongo database.
- backend chạy ở port `8999`.
- redis chạy ở port `6379`.

Có thể đổi username, password của service mongo để  đảm bảo an toàn (password không có ký tự đặc biệt), đảm bảo password ở cả mongodb và mongo-express giống nhau là được.

Kiểm tra các image và container:
```sh
docker images
```
![](images/docker-images.png)
```sh
docker ps
```
![](images/docker-container.png)

Kiểm tra log của backend:
```
docker logs -f face_kyc-api
```

![](images/docker-log-backend.png)

Trong phần log có thấy thông báo: `No such file or directory`, tuy nhiên chưa cần quan tâm vì sau khi deploy thì chưa có model indexing. Sau bước này có thể  đến mục 4. để test api luôn.

Lưu ý trường hợp mà sửa username và password của mongo trong file `docker-compose.yml` thì cũng cần phải sửa lại hai trường `admin_user` và `admin_password` trong file `env.json`

## 4. Test API

Để test các api được cấp có thể dùng Postman hoặc lệnh `curl`, mặc định sử dụng ip là `localhost`, nếu sử dụng ip local thì cần sửa lại ip tương ứng trong endpoint.

### 4.1. API đăng ký

API đăng ký là api giao tiếp giữa backend telehouse và backend của kotora.

- Endpoint: http://localhost:8999/api/user/pattern
- Method: POST
- Content-Type`: application/json
- Body:
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
- Response:
```json
{
    "message": "<message>",
    "connected": true
}
```

Tạo file `register.json` với nội dung:
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
Test với lệnh `curl`:
```sh
curl -d @register.json -X POST http://172.16.36.43:8999/api/user/pattern -H "Content-Type: application/json"
```

![](images/register-empty-images.png)

Trong đó: `connected` là thông báo kết nối từ backend kotora đến AI Box, do chưa có kết nối nên báo false, message đăng ký thành công nhưng trường `images` không chứa ảnh.

Sửa lại file `register.json` với nội dung:
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
Test với lệnh `curl`:
```sh
curl -d @register.json -X POST http://172.16.36.43:8999/api/user/pattern -H "Content-Type: application/json"
```

![](images/register-invalid-format.png)

Backend yêu cầu thông tin 2 trường: `zcfg_requester_address_email` và `zcfg_requester_id_passport` để tạo `user_id` cho người dùng theo công thức: `hash_md5(<cccd/cmnd>+"_"+<email>)`. Vì payload trên không có 2 trường này nên báo lỗi.

Sửa lại file `register.json` với nội dung:
```json
{
    "images": [],
    "zcfg_requester_comboname": "hoang_pham",
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
Test với lệnh `curl`:
```sh
curl -d @register.json -X POST http://172.16.36.43:8999/api/user/pattern -H "Content-Type: application/json"
```

![](images/register-update.png)

Update thông tin người dùng thành công, `invalid images` là do người dùng chưa có ảnh, hoặc ảnh không hợp lệ (AI box sẽ tiến hành verify), vấn đề này sau khi ghép nối với AI Box sẽ đánh giá sau.


### 4.2. API verify

API verify là api giao tiếp giữa backend và AI Box, cái này sẽ test sau.
- Endpoint: http://localhost:8999/api/user/pattern
- Method: PUT
- Content-Type: application/json
- Body:
```json
[
    {
        "face_images": ["<face_image_1>", "...", "<face_image_N>"],
        "gate_location": ["<gate_location_1>", "...", "<gate_location_N>"],
        "status": ["<status_1>", "...", "<status_N>"],
        "encodings": ["<encoding_1>", "...", "<encoding_N>"]
    },
    "...",
]
```
- Response:
```json
[
    [
        {
            "score": "<matching_score>",
            "user_id": ""
        },
        "...",
        {
            "face_images": "<face_image>",
            "gate_location": "<gate_location>",
            "score": "<matching_score>",
            "status": 1, //1 is checkin, 0 is checkout
            "timestamp": "%Y-%m-%d %H:%M:%S",
            "user_id": "<user_id>",
            "zcfg_requester_address_email": "<requester_email>",
            "zcfg_requester_comboname": "<requester_fullname>",
            "zcfg_requester_id_passport": "<cccd/cmnd>",
            "zcfg_requester_phone_number": "phone_number"
        }
    ],
    "...",
    [
        {
            "score": "<matching_score>",
            "user_id": ""
        },
        "...",
        {
            "face_images": "<face_image>",
            "gate_location": "<gate_location>",
            "score": "<matching_score>",
            "status": 1, //1 is checkin, 0 is checkout
            "timestamp": "%Y-%m-%d %H:%M:%S",
            "user_id": "<user_id>",
            "zcfg_requester_address_email": "<requester_email>",
            "zcfg_requester_comboname": "<requester_fullname>",
            "zcfg_requester_id_passport": "<cccd/cmnd>",
            "zcfg_requester_phone_number": "phone_number"
        }
    ]
]
```


### 4.3 API monitor log

Bên backend sẽ lưu lịch sử  các lần đăng ký, cập nhật thông tin cũng như xác minh (verify) người dùng. Bên telehouse có thể call API để lấy thông tin lịch sử.

- Endpoint: http://localhost:8999/api/user/monitor
- Method: POST, GET
- Content-Type: application/json
- Body:
```json
{
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
- Response:
```json
{
    "register_logs": [
        {},
        "...",
        {}
    ],
    "verify_logs": [
        {},
        "...",
        {}
    ]
}
```

Query thông tin lịch sử  theo những trường cần lấy, ví dụ:

Tạo file `monitor.json` với nội dung:
```json
{
    "zcfg_requester_address_email": "hoang@gmail.com"
}
```
Test với lệnh `curl`:
```sh
curl -d @monitor.json -X GET http://172.16.36.43:8999/api/user/monitor -H "Content-Type: application/json"
```

![](images/monitor.png)


Ở đây giá trị trường method là add (register) hoặc là edit (update), verify logs không có.

Có thể test thêm bằng cách query theo các trường khác, ví dụ như: `zcfg_approver_comboname`, `zend_date`, `zstart_date`, ...

### 4.4 Xóa người dùng:

API xóa người dùng khỏi hệ thống

- Endpoint: http://localhost:8999/api/user/pattern
- Method: DELETE
- Content-Type`: application/json
- Body:
```json
{
    "zcfg_requester_address_email": "<requester_email>",
    "zcfg_requester_id_passport": "<cccd/cmnd>",
}
```
- Response:
```json
{
    "message": "<message>",
    "email": "<address_email>",
    "id_passport": "<id_passport>"
}
```

Tạo file `delete.json` với nội dung:
```json
{
    "zcfg_requester_address_email": "hoang@gmail.com",
    "zcfg_requester_id_passport": ""
}
```
Test với lệnh `curl`:
```sh
curl -d @delete.json -X DELETE http://172.16.36.43:8999/api/user/pattern -H "Content-Type: application/json"
```

![](images/delete-user-invalid-format.png)

Lỗi do không đủ thông tin để xóa.

Sửa file `delete.json` với nội dung:
```json
{
    "zcfg_requester_address_email": "hoang@gmail.com",
    "zcfg_requester_id_passport": "038585963"
}
```
Test với lệnh `curl`:
```sh
curl -d @delete.json -X DELETE http://172.16.36.43:8999/api/user/pattern -H "Content-Type: application/json"
```

![](images/delete-user.png)

Test với lệnh `curl`:
```sh
curl -d @delete.json -X DELETE http://172.16.36.43:8999/api/user/pattern -H "Content-Type: application/json"
```

![](images/delete-user-not-exist.png)

Lỗi do user không tồn tại.
