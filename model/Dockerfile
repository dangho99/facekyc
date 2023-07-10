FROM nvcr.io/nvidia/l4t-ml:r32.7.1-py3

WORKDIR /app

COPY . .

RUN apt-get update -y && apt-get install libgeos-dev

RUN pip3 install -U pip && \
    pip3 install setuptools && \
    pip3 install -r requirements.txt

CMD ["python3", "main.py"]
