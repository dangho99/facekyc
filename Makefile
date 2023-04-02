SHELL := /bin/bash

VERSION := 1.0.0
OS := $(shell uname -m)

CAMERA_IMG = hoangph3/facekyc-camera
INDEXING_IMG = hoangph3/facekyc-indexing
RECOGNITION_IMG = hoangph3/facekyc-recognition

build_camera:
	docker build -f camera/Dockerfile.$(OS) -t $(CAMERA_IMG):$(OS)-$(VERSION) camera

build_indexing:
	docker build -f indexing/Dockerfile.$(OS) -t $(INDEXING_IMG):$(OS)-$(VERSION) indexing

build_recognition:
	docker build -f recognition/Dockerfile.base -t $(RECOGNITION_IMG):$(OS)-base recognition
	docker build -f recognition/Dockerfile.$(OS) -t $(RECOGNITION_IMG):$(OS)-$(VERSION) recognition

build: build_camera build_indexing build_recognition


push_camera:
	docker push $(CAMERA_IMG):$(OS)-$(VERSION)

push_indexing:
	docker push $(INDEXING_IMG):$(OS)-$(VERSION)

push_recognition:
	docker push $(RECOGNITION_IMG):$(OS)-base
	docker push $(RECOGNITION_IMG):$(OS)-$(VERSION)

push: push_camera push_indexing push_recognition

echo:
	@echo $(RECOGNITION_IMG):$(OS)-$(VERSION)

start:
	docker-compose -f docker-compose.$(OS).yml up -d

stop:
	docker-compose -f docker-compose.$(OS).yml down -v
