FROM hoangph3/face-kyc-api:v0.0.1

WORKDIR /app

COPY core /app/core
COPY certs /app/certs
COPY keeper /app/keeper
COPY util /app/util

COPY env.json /app/env.json
COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt

RUN apt-get update -y
RUN apt-get install nano telnet curl -y
RUN pip install -r requirements.txt

EXPOSE 8999

CMD ["python", "main.py"]