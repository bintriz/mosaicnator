import os
import hashlib


def make_dir(data_dir):
    os.makedirs(data_dir, exist_ok=True)

def checksum_match(data_file):
    dirname, filename = os.path.split(data_file)
    md5_file = '{}/checksum/{}.md5'.format(dirname, filename)
    if os.path.isfile(data_file) and os.path.isfile(md5_file):
        with open(data_file) as f:
            checksum_new = hashlib.md5(f.read().encode('utf-8')).hexdigest()
        with open(md5_file) as m:
            checksum_old = m.read().split()[0]
        return checksum_new == checksum_old
    else:
        return False
