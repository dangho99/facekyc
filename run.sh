docker run --rm --net=host \
-v $(pwd)/ansible:/data \
-v $(pwd)/certs:/data/certs \
hoangph3/ansible:$(uname -m)-2.10 ansible-playbook $1