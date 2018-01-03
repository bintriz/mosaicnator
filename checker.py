import os
import shlex
import subprocess 
from utils import make_dir

class Somatic:
    def __init__(self, args):
        self.ref = args.ref
        self.sample_file = args.infile
        self.chunk_on = args.chunk_on
        self.chunk_size = args.chunk_size
        self.var_type = args.var_type
        self.bams = set()

    @property
    def checker_name(self):
        return type(self).__name__.lower()

    def _check_ref(self):
        if not os.path.isfile(self.ref):
            msg = "Can't find the reference file '{}'".format(self.ref)
            raise FileNotFoundError(msg)
        if not os.path.isfile(self.ref + '.fai'):
            msg = "Can't find index for the fasta file '{}'".format(self.ref)
            raise FileNotFoundError(msg)
        refname = os.path.splitext(self.ref)[0]
        if not os.path.isfile(refname + '.dict'):
            msg = "Can't find dictionary for the fasta file '{}'".format(self.ref)
            raise FileNotFoundError(msg)
    
    def _extract_ref_SQ(self):
        sq = set()
        with open(self.ref + '.fai') as f:
            for line in f:
                chrom, length = line.split('\t')[:2]
                chrom = chrom.split(' ')[0]
                sq.add((chrom, length))
        self.ref_sq = sq

    def _check_sample_file(self):
        if not os.path.isfile(self.sample_file):
            msg = "Can't find the sample file '{}'".format(self.sample_file)
            raise FileNotFoundError(msg)

        with open(self.sample_file) as f:
            for line in f:
                try:
                    clone, tissue = line.strip().split('\t')[:2]
                    self.bams.add(clone)
                    self.bams.add(tissue)
                except ValueError as e:
                    msg = 'Sample list file should have at least 2 columns. Delimeter should be tab.'
                    raise e(msg)
    
    def _check_bams(self):
        for bam in self.bams:
            if not os.path.isfile(bam):
                msg = "Can't find the bam file '{}'".format(bam)
                raise FileNotFoundError(msg)

            bamname = os.path.splitext(bam)[0]
            if not os.path.isfile(bamname + '.bai') and not os.path.isfile(bamname + '.bam.bai'):
                msg = "Can't find index for the bam file '{}'".format(bam)
                raise FileNotFoundError(msg)

            if self._extract_bam_SQ(bam) != self.ref_sq:
                msg = ("SQ header in the bam file '{}'".format(bam) + 
                       "is not matched into the referece file '{}'".format(self.ref))
                raise ValueError(msg)

    @staticmethod
    def _extract_bam_SQ(bam):
        config = os.path.dirname(os.path.realpath(__file__)) + "/job.config"
        with open(config) as f:
            for line in f:
                if line[:9] == "SAMTOOLS=":
                    cmd = shlex.split(line[9:]) + ['view', '-H', bam]
                    break

        cmd_out = subprocess.run(cmd, universal_newlines=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            cmd_out.check_returncode()
        except subprocess.CallProcessError:
            sys.exit(cmd_out.stderr)

        sq = set()
        for line in cmd_out.stdout.split('\n'):
            if line[:3] == "@SQ":
                chrom = line.split('\t')[1][3:]
                length = line.split('\t')[2][3:]
                sq.add((chrom, length))
        return sq


    def _chunkfile(self):
        f=lambda n,i=0:"{:.0f}{}".format(n," kMG"[i])*(n<1e3)or f(n/1e3, i+1)
        chunk_file = "{}.call/genomic_regions_{}_chunk.txt".format(
            self.checker_name, f(self.chunk_size).strip())
        if not os.path.isfile(chunk_file):
            make_dir(os.path.dirname(chunk_file))
            with open(chunk_file, 'w') as out:
                with open(self.ref + '.fai') as f:
                    for line in f:
                        chrom, length = line.split('\t')[:2]
                        chrom = chrom.split(' ')[0]
                        length = int(length)
                        if chrom.replace("chr", "") in [str(i) for i in range(1, 23)] + ["X", "Y"]:
                            for start in range(1, length, self.chunk_size):
                                end = start + self.chunk_size - 1
                                if end > length:
                                    end = length
                                out.write('{}:{}-{}\n'.format(chrom, start, end))

    def _chromfile(self):
        chrom_file = "{}.call/genomic_regions_chrom.txt".format(self.checker_name)
        if not os.path.isfile(chrom_file):
            make_dir(os.path.dirname(chrom_file))
            with open(chrom_file, 'w') as out:
                with open(self.ref + '.fai') as f:
                    chroms = []
                    for line in f:
                        chrom, length = line.split()[:2]
                        length = int(length)
                        if chrom.replace("chr", "") in [str(i) for i in range(1, 23)] + ["X", "Y"]:
                            chroms.append((chrom, length))
                    chroms.sort(key=lambda chrom:chrom[1], reverse=True)
                for chrom, end in chroms:
                    out.write('{}:1-{}\n'.format(chrom, end))

    def run(self):
        print("Check reference: ", end="")
        self._check_ref()
        self._extract_ref_SQ()
        print("OK")
        print("Check sample list: ", end="")
        self._check_sample_file()
        self._check_bams()
        print("OK")
        if self.chunk_on:
            print("Prepare chunk list: ", end="")
            if self.var_type == "snv":
                self._chunkfile()
            elif self.var_type == "indel":
                self._chunkfile()
                self._chromfile()
            print("OK")

class Sensitivity(Somatic):
    def __init__(self, args):
        super().__init__(args)
        self.bams.add(args.control_bam)

    def _check_sample_file(self):
        if not os.path.isfile(self.sample_file):
            msg = "Can't find the sample file '{}'".format(self.sample_file)
            raise FileNotFoundError(msg)

        with open(self.sample_file) as f:
            for line in f:
                try:
                    clone = line.strip().split('\t')[0]
                    self.bams.add(clone)
                except ValueError as e:
                    msg = 'Sample list file should have at least 2 columns. Delimeter should be tab.'
                    raise e(msg)
        
class Pairwise(Somatic):    
    def __init__(self, args):
        super().__init__(args)

    def _check_sample_file(self):
        if not os.path.isfile(self.sample_file):
            msg = "Can't find the sample file '{}'".format(self.sample_file)
            raise FileNotFoundError(msg)

        with open(self.sample_file) as f:
            for line in f:
                try:
                    clone = line.strip().split('\t')[0]
                    self.bams.add(clone)
                except ValueError as e:
                    msg = 'Sample list file should have at least 2 columns. Delimeter should be tab.'
                    raise e(msg)
