import hashlib


def md5(s: str):
    s = hashlib.md5(s.encode()).hexdigest()
    return s
