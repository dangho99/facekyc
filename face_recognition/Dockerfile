FROM python:3.7

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install build-essential cmake pkg-config -y

RUN pip install -r requirements.txt

CMD [ "python", "main.py" ]
