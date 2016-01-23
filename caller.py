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
    def __init__(self, ref, prefix, min_MQ, min_BQ, skip_on, chunk_file=None):
        self.ref = ref
        self.prefix = prefix
        self.min_MQ = min_MQ
        self.min_BQ = min_BQ
        self.skip_on = skip_on
        self.chunk_file = chunk_file
        self.q = GridEngineQueue()
        self.script_dir = '{}/job_scripts'.format(
            os.path.dirname(os.path.realpath(__file__)))
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
    def coord_file(self):
        return '{}/{}.{}.snv_coord.txt'.format(
            self.af_dir, self.sample_name, self.caller_name)

    @property
    def af_file(self):
        return '{}/{}.{}.snv_AF.txt'.format(
            self.af_dir, self.sample_name, self.caller_name)

    @property
    def af_file_ok(self):
        return self.skip_on and checksum_match(self.af_file)

    @property
    def chunk_n(self):
        return sum(1 for line in open(self.chunk_file))
    
    def _qopt(self, jprefix, hold_jid=''):
        qopt = '-N {}_{}.{} -e {} -o {}'.format(
            jprefix, self.caller_name, self.sample_name, self.qerr_dir, self.qout_dir)
        if hold_jid == '':
            return qopt
        else:
            return qopt + ' -hold_jid {}'.format(hold_jid)

    def _call(self):
        qopt = self._qopt('run')
        if self.chunk_file is not None:
            qopt = qopt + ' -t 1-{}'.format(self.chunk_n)
            cmd = '{}/run_{}_chunk.sh {} {} {} {} {}'.format(
                self.script_dir, self.caller_name,
                self.ref, self.clone, self.tissue,
                self.call_outname, self.chunk_file)
        else:
            cmd = '{}/run_{}.sh {} {} {} {}'.format(
                self.script_dir, self.caller_name,
                self.ref, self.clone, self.tissue,
                self.call_outname)
        return self.q.submit(qopt, cmd)

    def _post(self, hold_jid):
        qopt = self._qopt('post', hold_jid)
        if self.chunk_file is not None:
            cmd = '{}/post_{}_chunk.sh {} {}'.format(
                self.script_dir, self.caller_name,
                self.call_outname, self.chunk_file)
        else:
            cmd = '{}/post_{}.sh {}'.format(
                self.script_dir, self.caller_name,
                self.call_outname)
        return self.q.submit(qopt, cmd)
            
    def _coord(self, hold_jid):
        qopt = self._qopt('coord', hold_jid)
        cmd = '{}/snv_coord_{}.sh {} {}'.format(
            self.script_dir, self.caller_name, self.call_file, self.coord_file)
        return self.q.submit(qopt, cmd)

    def _af(self, hold_jid):
        qopt = self._qopt('af', hold_jid)
        cmd = '{}/snv_af.sh {} {} {} {} {} {}'.format(
            self.script_dir, self.min_MQ, self.min_BQ, self.clone, self.tissue,
            self.coord_file, self.af_file)
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
        
        hold_jid = ''

        if self.af_file_ok:
            self._skip_msg('calling')
            self._skip_msg('af_calc')
        else:
            if self.call_file_ok:
                self._skip_msg('calling')
            else:
                make_dir(self.qerr_dir)
                make_dir(self.qout_dir)
                make_dir(self.call_dir)        
                hold_jid = self._call()
                hold_jid = self._post(hold_jid)
                self._run_msg('calling')
                
            hold_jid = self._coord(hold_jid)
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
        return '{}.snp.Somatic.hc'.format(self.call_outname)

    @property
    def call_file_indel(self):
        return '{}.indel.Somatic.hc'.format(self.call_outname)

    @property
    def call_file_ok(self):
        return (self.skip_on and
                checksum_match(self.call_file) and
                checksum_match(self.call_file_indel))

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
        return '{}/results/passed.somatic.snvs.vcf'.format(self.call_outname)

    @property
    def call_file_indel(self):
        return '{}/results/passed.somatic.indels.vcf'.format(self.call_outname)

    @property
    def call_file_ok(self):
        return (self.skip_on and
                checksum_match(self.call_file) and
                checksum_match(self.call_file_indel))

    def _post(self, hold_jid):
        return hold_jid
