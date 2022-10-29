FROM hoangph3/face-recognition-gateway:v0.0.1

WORKDIR /app

COPY . .

RUN apt-get update -y && pip install --upgrade pip && apt-get install telnet nano curl -y

RUN pip install setuptools
RUN pip install -r requirements.txt

CMD [ "python", "main.py" ]
