#! /bin/bash

mkcert -install

mkcert -cert-file cert.pem \
  -key-file key.pem \
  localhost 127.0.0.1 \
  192.168.0.4 \
  192.168.0.7 \
  192.168.0.8 \
  192.168.0.20 \
  192.168.0.21 \
  192.168.0.22 \
  192.168.0.23
