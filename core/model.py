import face_recognition
from PIL import Image
from kafka import KafkaConsumer
import json
from util.dataio import convert_bytes_to_numpy_array


def face_detection():
    consumer = KafkaConsumer(
        'secret_data',
        bootstrap_servers='localhost:9092',
        # auto_offset_reset='earliest',
        auto_offset_reset="earliest",
        # enable_auto_commit=True,
        client_id='hoangp46',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    for event in consumer:
        event_data = event.value
        userid = event_data["userid"]
        username = event_data["username"]
        userimg = convert_bytes_to_numpy_array(event_data["img"])
        face_locations = face_recognition.face_locations(userimg)
        for face_location in face_locations:
            top, right, bottom, left = face_location
            face_image = userimg[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
            pil_image.show()