FROM hoangph3/python-opencv:py3.7-cv4.0.0

WORKDIR /app

COPY . .

RUN apt-get update -y && \
    apt-get install nano telnet curl -y && \
    pip install -r requirements.txt

CMD ["python", "main.py"]
