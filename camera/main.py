import cv2
import json
import requests
import numpy as np
import imutils
from loguru import logger
import os
import time

from util.controller import create_worker_process
from util.dataio import convert_numpy_array_to_bytes, resize_image


os.environ['DISPLAY'] = ':0'
requests.packages.urllib3.disable_warnings()
# Log
logger.add('app.log', rotation="500 MB")


def read_frame(config: dict):

    # gpio
    try:
        from util import gpio_handler
        gpio_handler.init_gpio()
        gpio_imported = True
    except Exception as e:
        gpio_imported = False
        logger.warning(str(e))

    # resize
    new_width = int(os.getenv("IMAGE_WIDTH", "500"))

    # get camera
    camera = {}
    for k, cam in config.items():
        if 'http' not in str(cam['host']):
            camera["{}_{}".format(k, cam['id'])] = cv2.VideoCapture(cam['host'])
        else:
            camera["{}_{}".format(k, cam['id'])] = cam['host']

    logger.info("Camera: {}".format(camera))

    try:
        while True:
            data = {}
            for name_capture, video_capture in camera.items():
                if isinstance(video_capture, str):
                    try:
                        img_resp = requests.get(video_capture)
                        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
                        img = cv2.imdecode(img_arr, -1)
                        # resize
                        height, width, channel = img.shape
                        aspect_ratio = height / width
                        new_height = new_width * aspect_ratio
                        img = imutils.resize(img, width=int(new_width), height=int(new_height))
                        # cv2.imshow(name_capture, img)  # not working with docker because it not have GUI
                        
                        data[name_capture] = img
                    except Exception as e:
                        pass
                else:
                    ret, img = video_capture.read()
                    if ret:
                        # resize
                        img = resize_image(img, new_width)
                        data[name_capture] = img
                        # cv2.imshow(name_capture, img)  # not working with docker because it not have GUI

            response = {}
            connected = {}
            for task, payload in data.items():
                connected[task] = True
                try:
                    r = requests.put(
                        url=os.getenv("SERVING_URL", "https://127.0.0.1:8501/api/user/pattern"),
                        json={
                            "images": [convert_numpy_array_to_bytes(payload)],
                            "cam_cfg": config[name_capture.split('_')[0]]
                        },
                        verify=False
                    )
                    response[task] = r.json()
                except:
                    connected[task] = False

            # log result
            result = {'connected': connected, 'response': response}
            logger.info(json.dumps(result))

            # open gate
            for _task, _response in response.items():

                for each_frame in _response['responses']:
                    if not len(each_frame):
                        continue

                    for each_user in each_frame:
                        if not each_user.get('active', None):  # user is not actived in database
                            continue

                        if gpio_imported:
                            try:
                                gpio_handler.open_gate(each_user.get('gate_location', None))
                            except Exception as e:
                                logger.info("Open gate error: {} with user: {}".format(str(e), each_user))

            # Press Esc key to exit
            if cv2.waitKey(1) == 27:
                break

            time.sleep(1 / int(os.getenv("FPS", 1)))

    except KeyboardInterrupt:
        for name_capture, video_capture in camera.items():
            if isinstance(video_capture, str):
                continue
            video_capture.release()
        cv2.destroyAllWindows()

        if gpio_imported:
            try:
                gpio_handler.clean_gpio()
            except:
                pass

        logger.info("KeyboardInterrupt")


if __name__ == "__main__":
    # Read config
    with open("config/env.json") as f:
        configs = json.load(f)

    # Capture frames
    # for config in configs['camera']:
    #     for k, v in config.items():
    #         create_worker_process(k, read_frame, (config, ))

    # Support only 1 thread
    read_frame(config=configs['camera'][0])
