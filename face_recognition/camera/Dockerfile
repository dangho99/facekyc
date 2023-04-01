FROM jjanzic/docker-python3-opencv:opencv-4.0.0

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install nano telnet curl -y && \
    pip install -U pip && \
    pip install -r requirements.txt

CMD ["python", "main.py"]
