FROM python:3.8-slim-buster

WORKDIR /app

COPY . . 

RUN apt-get update -y
RUN apt-get install nano telnet -y
RUN pip install -r requirements.txt

EXPOSE 8999

CMD ["python", "main.py"]