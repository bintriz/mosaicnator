import os
import hashlib


def make_dir(data_dir):
    os.makedirs(data_dir, exist_ok=True)

def check_dir(data_dir):
    if os.path.isdir(data_dir):
        return
    else:
        msg = "Can't find the data directory '{}'".format(data_dir)
        raise FileNotFoundError(msg)

def check_bam_index(bam_file):
    file_stem = os.path.splitext(bam_file)[0]
    if os.path.isfile(file_stem + '.bai') or os.path.isfile(file_stem + '.bam.bai'):
        return
    else:
        msg = "Can't find index for the BAM file '{}'".format(bam_file)
        raise FileNotFoundError(msg)

def check_ref_index(fasta_file):
    if os.path.isfile(fasta_file + '.fai'):
        return
    else:
        msg = "Can't find index for the fasta file '{}'".format(fasta_file)
        raise FileNotFoundError(msg)

def check_ref_dict(fasta_file):
    file_stem = os.path.splitext(fasta_file)[0]
    if os.path.isfile(file_stem + '.dict'):
        return
    else:
        msg = "Can't find dictionary for the fasta file '{}'".format(fasta_file)
        raise FileNotFoundError(msg)

def read_sample_pairs(sample_file):
    with open(sample_file) as f:
        pairs = []
        for line in f:
            try:
                clone, tissue = line.split()[:2]
            except ValueError as e:
                msg = 'Sample pairs file should have at least 2 columns.'
                raise e(msg)
            pairs.append((clone, tissue))
        return pairs

def read_samples(sample_file):
    with open(sample_file) as f:
        samples = []
        for line in f:
            try:
                sample = line.split()[0]
            except ValueError as e:
                msg = 'There is empty row.'
                raise e(msg)
            samples.append(sample)
        return samples
    
def get_chunk_intervals(fai_file, chunk_size):
    with open(fai_file) as f:
        intervals = []
        for line in f:
            chrom, chrom_size = line.split()[:2]
            chrom_size = int(chrom_size)
            for start in range(1, chrom_size, chunk_size):
                end = start + chunk_size - 1
                if end > chrom_size:
                    end = chrom_size
                intervals.append((chrom, start, end))
        return intervals

def get_samplename(clone, tissue):
    clname = os.path.splitext(os.path.basename(clone))[0]
    tiname = os.path.splitext(os.path.basename(tissue))[0]
    return '{}_-_{}'.format(clname, tiname)

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