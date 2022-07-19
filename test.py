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
    filepath = "/home/ph3/Desktop/face_kyc_api/broker/data/hoangph_1211/img_1.jpg"
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
    data_dir = "/home/ph3/Desktop/face_kyc_api/broker/data"
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
        bootstrap_servers='localhost:9092',
        client_id='hoangp46',
        value_deserializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(consumer.topics())


if __name__ == "__main__":
    # test_io()
    # test_producer()
    test_consumer()