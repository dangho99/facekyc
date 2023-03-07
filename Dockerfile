FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN apt-get update -y
RUN apt-get install nano telnet curl -y
RUN pip install -r requirements.txt

EXPOSE 8999

CMD ["python", "main.py"]
