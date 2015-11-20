import os

def make_dir(dir):
    os.makedirs(dir, exist_ok=True)

def make_qdir(subdir=''):
    make_dir(os.path.join('q.err', subdir))
    make_dir(os.path.join('q.out', subdir))

def check_dir(dir):
    if os.path.isdir(dir):
        return
    else:
        msg = "Can't find the data directory '{}'".format(dir)
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

def check_outfile(file):
    if not os.path.isfile(file):
        return
    else:
        msg = ("Out file '{}' already exists. "
               "If you want to rerun, "
               "the remove old out file first.").format(file)
        raise FileExistsError(msg)

def read_sample_pairs(file):
    with open(file) as f:
        pairs = []
        for line in f:
            try:
                clone, tissue = line.split()[:2]
            except ValueError as e:
                msg = 'Sample pairs file should have at least 2 columns.'
                raise e(msg)
            pairs.append((clone, tissue))
        return pairs

def read_samples(file):
    with open(file) as f:
        samples = []
        for line in f:
            try:
                sample = line.split()[0]
            except ValueError as e:
                msg = 'There is empty row.'
                raise e(msg)
            samples.append(sample)
        return samples

def read_header(file, n=1):
    with open(file) as f:
        while n > 0:
            yield f.readline()
            n -= 1

def read_body(file, start=2):
    with open(file) as f:
        for line in f:
            if start > 1:
                start -= 1
                continue
            yield line

def read_vcf_header(vcf):
    with open(vcf) as f:
        for line in f:
            if line[0] != '#':
                break
            yield line

def read_vcf_body(vcf):
    with open(vcf) as f:
        for line in f:
            if line[0] == '#':
                continue
            yield line
    
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

def get_samplename(file):
    return os.path.splitext(os.path.basename(file))[0]
