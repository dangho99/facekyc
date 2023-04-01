FROM hoangph3/face-recognition:base

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install libgeos-dev telnet nano curl -y

RUN pip install setuptools && \
    pip install -r requirements.txt

CMD [ "python", "main.py" ]
