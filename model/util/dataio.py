from PIL import Image, ExifTags
from loguru import logger
import numpy as np
import socket
import base64
import io
import cv2


def convert_img_to_numpy_array(img_path, new_width=500):
    # TODO: load image from directory and convert to numpy array
    img = Image.open(img_path)
    img.convert("RGB").save(img_path, "JPEG")
    img = Image.open(img_path)

    # resize with aspect ratio
    aspect_ratio = img.height / img.width
    new_height = new_width * aspect_ratio
    img = img.resize((int(new_width), int(new_height)))

    # convert to array
    array = np.asarray(img)
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


def resize_image(img: np.ndarray, new_width=500):
    height, width, channel = img.shape
    aspect_ratio = height / width
    new_height = new_width * aspect_ratio
    resized_img = cv2.resize(img, (int(new_width), int(new_height)))
    return resized_img


def send_socket(address, msg):
    if isinstance(msg, str):
        msg = msg.encode()
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.sendto(msg, address)
    return

def base64_str_to_cv2(base64_str):
    try:
        compressed_data = base64.b64decode(base64_str)
        img_pil = Image.open(io.BytesIO(compressed_data))
        img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        if img_pil._getexif() is not None:
            exif = dict((ExifTags.TAGS[k], v) for k, v in img_pil._getexif().items() if k in ExifTags.TAGS)
            orientation = exif.get("Orientation", None)
            if orientation == 3:
                img = cv2.rotate(img, cv2.ROTATE_180)
            elif orientation == 6:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif orientation == 8:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    except Exception as e:
        logger.error(str(e))
        return 
    else:
        return img