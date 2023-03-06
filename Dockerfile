FROM hoangph3/face-kyc-api:1.0.0

WORKDIR /app

COPY . .

RUN apt-get update -y
RUN apt-get install nano telnet curl -y
RUN pip install -r requirements.txt

EXPOSE 8999

CMD ["python", "main.py"]
