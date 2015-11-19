import os

def check_dir(dir):
    os.makedirs(dir, exist_ok=True)

def check_qdir(subdir=''):
    check_dir(os.path.join('q.err', subdir))
    check_dir(os.path.join('q.out', subdir))

def check_bam_index(bam_file):
    file_stem = os.path.splitext(bam_file)[0]
    if os.path.isfile(file_stem + '.bai') or os.path.isfile(file_stem + '.bam.bai'):
        return
    else:
        msg = "Can't find ndex for BAM file '{}'".format(bam_file)
        raise FileNotFoundError(msg)

def check_ref_index(fasta_file):
    if os.path.isfile(fasta_file + '.fai'):
        return
    else:
        msg = "Can't find index for fasta file '{}'".format(fasta_file)
        raise FileNotFoundError(msg)

def check_ref_dict(fasta_file):
    file_stem = os.path.splitext(fasta_file)[0]
    if os.path.isfile(file_stem + '.dict'):
        return
    else:
        msg = "Can't find dictionary for fasta file '{}'".format(fasta_file)
        raise FileNotFoundError(msg)
        
def parse_sample_list_file(file):
    with open(file) as f:
        return [line.split() for line in f]

def get_chunk_intervals(fai, chunk_size):
    with open(fai) as f:
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

