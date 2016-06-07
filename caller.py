import os
from abc import (
    ABCMeta,
    abstractmethod)
from job_queue import GridEngineQueue
from utils import (
    make_dir,
    checksum_match,
    skip_msg,
    run_msg)


class Caller(metaclass=ABCMeta):
    def __init__(self, args, prefix, chunk_file=None):
        self.prefix = prefix
        self.var_type = args.var_type
        self.ref = args.ref
        self.min_MQ = args.min_MQ
        self.min_BQ = args.min_BQ
        self.skip_on = args.skip_on
        self.chunk_file = chunk_file
        self.q = GridEngineQueue()
        make_dir(self.af_dir)

    @property
    def caller_name(self):
        return type(self).__name__.lower()

    @property
    def sample_name(self):
        clname = os.path.splitext(os.path.basename(self.clone))[0]
        tiname = os.path.splitext(os.path.basename(self.tissue))[0]
        return '{}_-_{}'.format(clname, tiname)

    @property
    def bin_path(self):
        return os.path.dirname(os.path.realpath(__file__))

    @property
    def script_dir(self):
        return '{}/job_scripts/{}'.format(self.bin_path, self.caller_name)
        
    @property
    def qerr_dir(self):
        return 'q.err/{}.{}'.format(self.sample_name, self.caller_name)

    @property
    def qout_dir(self):
        return 'q.out/{}.{}'.format(self.sample_name, self.caller_name)
    
    @property
    def call_dir(self):
        return '{}.call/{}.{}'.format(
            self.prefix, self.sample_name, self.caller_name)

    @property
    def af_dir(self):
        return '{}.AF'.format(self.prefix)

    @property
    def call_outname(self):
        return '{}/{}.{}'.format(
            self.call_dir, self.sample_name, self.caller_name)
    
    @property
    @abstractmethod
    def call_file(self):
        ...

    @property
    def call_file_ok(self):
        return self.skip_on and checksum_match(self.call_file)

    @property
    def af_file(self):
        return '{}/{}.{}.{}_AF.txt'.format(
            self.af_dir, self.sample_name, self.caller_name, self.var_type)

    @property
    def af_file_ok(self):
        return self.skip_on and checksum_match(self.af_file)

    @property
    def chunk_n(self):
        n = sum(1 for line in open(self.chunk_file))
        if n == 0:
            raise RuntimeError("{} has no chunk info. Delete it and rerun.".format(self.chunk_file))
        return n
    
    def _qopt(self, jprefix, hold_jid=''):
        qopt = '-N {}_{}.{} -e {} -o {} -v BIN_PATH={}'.format(
            jprefix, self.caller_name, self.sample_name, self.qerr_dir, self.qout_dir, self.bin_path)
        if hold_jid == '':
            return qopt
        else:
            return qopt + ' -hold_jid {}'.format(hold_jid)

    def _call(self):
        qopt = self._qopt('call')
        if self.chunk_file is not None:
            qopt = qopt + ' -t 1-{}'.format(self.chunk_n)
            cmd = '{}/call_chunk.sh {} {} {} {} {}'.format(
                self.script_dir, self.ref, self.clone, self.tissue,
                self.call_outname, self.chunk_file)
        else:
            cmd = '{}/call.sh {} {} {} {}'.format(
                self.script_dir, self.ref, self.clone, self.tissue,
                self.call_outname)
        return self.q.submit(qopt, cmd)

    def _post(self, hold_jid):
        qopt = self._qopt('post', hold_jid)
        if self.chunk_file is not None:
            cmd = '{}/post_chunk.sh {} {}'.format(
                self.script_dir, self.call_outname, self.chunk_file)
        else:
            cmd = '{}/post.sh {}'.format(
                self.script_dir, self.call_outname)
        return self.q.submit(qopt, cmd)
            
    def _af(self, hold_jid):
        qopt = self._qopt('af', hold_jid)
        if self.var_type == "snv":
            cmd = '{}/snv_af.sh {} {} {} {} {} {}'.format(
                self.script_dir, self.min_MQ, self.min_BQ,
                self.clone, self.tissue, self.call_file, self.af_file)
        elif self.var_type == "indel":
            cmd = '{}/indel_af.sh {} {} {}'.format(
                self.script_dir, self.ref, self.call_file, self.af_file)            
        return self.q.submit(qopt, cmd)

    def _skip_msg(self, jname):
        if self.q.__class__.is_1st_print:
            self.q.__class__.is_1st_print = False
        else:
            print('\x1b[2A', end='\r')
        skip_msg(jname, '{}.{}'.format(self.sample_name, self.caller_name))

    def _run_msg(self, jname):
        run_msg(jname, '{}.{}'.format(self.sample_name, self.caller_name))
        
    def run(self, clone, tissue):
        self.clone = clone
        self.tissue = tissue
        make_dir(self.qerr_dir)
        make_dir(self.qout_dir)
        make_dir(self.call_dir)        
        
        hold_jid = ''

        if self.af_file_ok:
            self._skip_msg('calling')
            self._skip_msg('af_calc')
        else:
            if self.call_file_ok:
                self._skip_msg('calling')
            else:
                hold_jid = self._call()
                hold_jid = self._post(hold_jid)
                self._run_msg('calling')
                
            hold_jid = self._af(hold_jid)
            self._run_msg('af_calc')

        return hold_jid

class MuTect(Caller):
    @property
    def call_file(self):
        return '{}.keep.txt'.format(self.call_outname)

class VarScan(Caller):
    @property
    def call_file(self):
        if self.var_type == "snv":
            var_type = "snp"
        else:
            var_type = self.var_type
        return '{}.{}.Somatic.hc'.format(
            self.call_outname, var_type)

class SomaticSniper(Caller):
    @property
    def call_file(self):
        return '{}.somatic.vcf'.format(self.call_outname)

class Strelka(Caller):
    @property
    def call_outname(self):
        return self.call_dir

    @property
    def call_file(self):
        return '{}/results/passed.somatic.{}s.vcf'.format(
            self.call_outname, self.var_type)

    def _post(self, hold_jid):
        return hold_jid

class Scalpel(Caller):
    @property
    def call_file(self):
        return '{}/somatic.5x.indel.vcf.gz'.format(
            self.call_dir)
    
    def _call(self):
        if self.chunk_file is not None:
            chrom_sizes = [
                int(line.split('-')[1]) for line in open(self.chunk_file)]
            qopt_param_by_min_size = {
                180000000: {"queue": "lg-mem", "threads": 20, "h_vmem": "16G"},
                100000000: {"queue": "4-days", "threads": 20, "h_vmem": "10G"},
                 10000000: {"queue": "4-days", "threads": 10, "h_vmem": "10G"},
                        1: {"queue": "4-days", "threads":  4, "h_vmem":  "8G"}}
            start = 1
            jids = []
            for min_size in sorted(qopt_param_by_min_size.keys(), reverse=True):
                end = [i for i, size in enumerate(chrom_sizes, 1)
                       if size >= min_size][-1]
                qopt_param_by_min_size[min_size]["start"] = start 
                qopt_param_by_min_size[min_size]["end"] = end
                start = end + 1
                qopt = " ".join([
                    self._qopt('call'), "-t {start}-{end}", "-q {queue}",
                    "-pe threaded {threads}", "-l h_vmem={h_vmem}"]
                ).format(**qopt_param_by_min_size[min_size])
                cmd = '{}/call_chunk.sh {} {} {} {} {} {}'.format(
                    self.script_dir, self.ref, self.clone, self.tissue,
                    self.call_outname, self.chunk_file,
                    qopt_param_by_min_size[min_size]["threads"])
                jids.append(self.q.submit(qopt, cmd))
            hold_jid = ",".join(jids)
        else:
            qopt = self._qopt('call')
            cmd = '{}/call.sh {} {} {} {}'.format(
                self.script_dir, self.ref, self.clone, self.tissue,
                self.call_outname)
            hold_jid = self.q.submit(qopt, cmd)
        return hold_jid
        
    def _post(self, hold_jid):
        qopt = self._qopt('post', hold_jid)
        if self.chunk_file is not None:
            cmd = '{}/post_chunk.sh {} {} {}'.format(
                self.script_dir, self.ref, self.call_outname, self.chunk_file)
        else:
            cmd = '{}/post.sh {} {}'.format(
                self.script_dir, self.ref, self.call_outname)
        return self.q.submit(qopt, cmd) 
