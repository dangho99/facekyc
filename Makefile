SHELL := /bin/bash

TAG = 1.0.0

CAMERA_IMG = hoangph3/facekyc-camera:$(TAG)

INDEXING_IMG = hoangph3/facekyc-indexing:$(TAG)

RECOGNITION_IMG = hoangph3/facekyc-recognition:$(TAG)

BASE_IMG = hoangph3/facekyc-recognition:base


build_camera:
	docker build -f camera/Dockerfile -t $(CAMERA_IMG) camera
build_indexing:
	docker build -f indexing/Dockerfile -t $(INDEXING_IMG) indexing
build_recognition:
	docker build -f recognition/Dockerfile -t $(RECOGNITION_IMG) recognition
build_base:
	docker build -f recognition/Dockerfile.base -t $(BASE_IMG) recognition
build: build_camera build_indexing build_recognition


push_camera:
	docker push $(CAMERA_IMG)
push_indexing:
	docker push $(INDEXING_IMG)
push_recognition:
	docker push $(RECOGNITION_IMG)
push_base:
	docker push $(BASE_IMG)
push: push_camera push_indexing push_recognition


pull_camera:
	docker pull $(CAMERA_IMG)
pull_indexing:
	docker pull $(INDEXING_IMG)
pull_recognition:
	docker pull $(RECOGNITION_IMG)
pull_base:
	docker pull $(BASE_IMG)
pull: pull_camera pull_indexing pull_recognition
