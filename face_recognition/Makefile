SHELL := /bin/bash

TAG = 1.0.0
CAMERA_IMG = hoangph3/face-camera:$(TAG)
RECOGNITION_IMG = hoangph3/face-recognition:$(TAG)

build_face_camera:
	docker build -f camera/Dockerfile -t $(CAMERA_IMG) camera
build_face_recognition:
	docker build -f model/Dockerfile -t $(RECOGNITION_IMG) model

push_face_camera:
	docker push $(CAMERA_IMG)
push_face_recognition:
	docker push $(RECOGNITION_IMG)
