FROM hoangph3/facekyc-camera:x86_64-base

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install nano telnet curl -y && \
    pip install -r requirements.txt

CMD ["python", "main.py"]
