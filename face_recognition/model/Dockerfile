FROM hoangph3/face-recognition-gateway:v0.0.1

WORKDIR /app

COPY . .

# RUN apt-get update -y && apt-get install telnet nano curl -y

RUN pip install --upgrade pip && pip install setuptools
RUN pip install -r requirements.txt

CMD [ "python", "main.py" ]
