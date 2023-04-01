FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install nano telnet curl -y && \
    pip install -r requirements.txt

CMD ["python", "main.py"]
