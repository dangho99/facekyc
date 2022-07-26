docker pull tensorflow/serving;

docker run -dp 9501:8501 --name=face_recognition_serving -v "$(pwd)/:/models/" -t tensorflow/serving \
--model_config_file=/models/models.config \
--model_config_file_poll_wait_seconds=60

