FROM node:14

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install cmake apt-utils -y && \
    apt-get install ffmpeg -y && \
    apt-get install libavcodec-dev libavformat-dev libavdevice-dev libgtk2.0-dev pkg-config -y

RUN npm install 
