from PIL import Image
import numpy as np
import base64
import io


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
