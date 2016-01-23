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
            try:
                checksum_old = m.read().split()[0]
            except IndexError:
                checksum_old = ''
        return checksum_new == checksum_old
    else:
        return False

def skip_msg(jname, msg):
    print('\x1b[2K', end='\r')
    print('Skip {:>16} job: {}\n\n'.format(jname, msg))

def run_msg(jname, msg):
    print('\x1b[2A', end='\r')
    print('\x1b[2K', end='\r')
    print('Submitted {:>11} job: {}\n\n'.format(jname, msg))

def end_msg(jtotal):
    print('\x1b[2A', end='\r')
    print('\x1b[2K', end='\r')
    print('-' * 59)
    print('\x1b[2K', end='\r')
    print('mosaicnator.py submitted {} jobs in total.'.format(jtotal))
