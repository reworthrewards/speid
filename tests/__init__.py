import os

with open('tests/conf_files/pk.pem') as fp:
    private_key = fp.read()
os.environ['STP_PRIVATE_KEY'] = private_key
