FROM hoangph3/facekyc-recognition:x86_64-base

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install libgeos-dev telnet nano curl -y && \
    pip install setuptools && \
    pip install -r requirements.txt

CMD [ "python", "main.py" ]
