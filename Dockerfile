FROM hoangph3/face-kyc-api:v0.0.1

WORKDIR /app

COPY . .

RUN apt-get update -y
RUN apt-get install nano telnet curl -y
RUN pip install -r requirements.txt

EXPOSE 8999

CMD ["python", "main.py"]