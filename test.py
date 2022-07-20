from util.dataio import (
    convert_img_to_numpy_array,
    convert_numpy_array_to_bytes,
    convert_bytes_to_numpy_array,
    convert_img_to_bytes
)
import os
import json
from kafka import KafkaProducer, KafkaConsumer


def test_io():
    filepath = "/home/hoang/Desktop/face_kyc_api/broker/data/hoangph_1211/img_1.jpg"
    img = convert_img_to_numpy_array(filepath)
    print(img.shape)
    j_dumps = convert_numpy_array_to_bytes(img)
    print(j_dumps, type(j_dumps))
    j_loads = convert_bytes_to_numpy_array(j_dumps)
    print(j_loads.shape)


def test_producer():
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        client_id='hoangp46',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    data_dir = "/home/hoang/Desktop/face_kyc_api/broker/data"
    for username in os.listdir(data_dir):
        user_dir = os.path.join(data_dir, username)
        user_id = username.split('_')[1]
        email_id = username.split('_')[0]
        for img in os.listdir(user_dir):
            img_path = os.path.join(user_dir, img)
            fake_data = {
                "userid": user_id,
                "username": email_id,
                "img": convert_img_to_bytes(img_path)
            }
            producer.send("secret_data", fake_data)


def test_consumer():
    consumer = KafkaConsumer(
        'secret_data',
        bootstrap_servers='localhost:9092',
        # auto_offset_reset='earliest',
        auto_offset_reset="earliest",
        # enable_auto_commit=True,
        client_id='hoangp46',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )
    print(consumer.topics())
    for event in consumer:
        event_data = event.value
        for key, value in event_data.items():
            if key == "img":
                img = convert_bytes_to_numpy_array(value)
                print(img.shape)
            else:
                print("{}: {}".format(key, value))
        print()
        input("Press Enter to continue...")


if __name__ == "__main__":
    # test_io()
    # test_producer()
    # test_consumer()
    from core.model import face_detection
    face_detection()