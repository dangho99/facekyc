FROM ubuntu:18.04

WORKDIR /app

COPY . .

ENV DEBIAN_FRONTEND=noninteractive
ENV LIBGL_ALWAYS_INDIRECT=1

RUN apt-get update && apt-get install -y python3-pyqt5 python3-pip3

RUN pip3 install -U pip && pip3 install -r requirements.txt

CMD [ "python3", "main.py" ]
