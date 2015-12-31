import os
from abc import (
    ABCMeta,
    abstractmethod)
from job_queue import GridEngineQueue
from utils import (
    make_dir,
    checksum_match)


class Caller(metaclass=ABCMeta):
    def __init__(self, ref, prefix, skip_on, chunk_on=False):
        self.ref = ref
        self.refidx = ref + '.fai'
        self.prefix = prefix
        self.skip_on = skip_on
        self.chunk_on = chunk_on
        self.chunk_size = 25000000
        self.q = GridEngineQueue()
        self.script_dir = '{}/job_scripts'.format(
            os.path.dirname(os.path.realpath(__file__)))
        self.hold_jid = {}
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
    def intervals(self):
        with open(self.refidx) as f:
            for line in f:
                chrom, chrom_size = line.split()[:2]
                chrom_size = int(chrom_size)
                for start in range(1, chrom_size, self.chunk_size):
                    end = start + self.chunk_size - 1
                    if end > chrom_size:
                        end = chrom_size
                    yield (chrom, start, end)

    def _qopt(self, jprefix, hold_jid=''):
        qopt = '-N {}_{}.{} -e {} -o {}'.format(
            jprefix, self.caller_name, self.sample_name, self.qerr_dir, self.qout_dir)
        if hold_jid == '':
            return qopt
        else:
            return qopt + ' -hold_jid {}'.format(hold_jid)

    def _call_chunk(self):
        jids = []
        for chrom, start, end in self.intervals:
            chunktag = '{}-{}-{}'.format(chrom, start, end)
            interval = '{}:{}-{}'.format(chrom, start, end)
            qopt = '-N run_{}.{}.{} -e {} -o {}'.format(
                self.caller_name, self.sample_name, chunktag,
                self.qerr_dir, self.qout_dir)
            cmd = '{}/run_{}_chunk.sh {} {} {} {}.{} {}'.format(
                self.script_dir, self.caller_name,
                self.ref, self.clone, self.tissue, 
                self.call_outname, chunktag, interval)
            jids.append(self.q.submit(qopt, cmd))
        return ','.join(jids)

    def _call(self):
        if self.chunk_on:
            return self._call_chunk()
        else:
            qopt = self._qopt('run')
            cmd = '{}/run_{}.sh {} {} {} {}'.format(
                self.script_dir, self.caller_name,
                self.ref, self.clone, self.tissue, self.call_outname)
            return self.q.submit(qopt, cmd)

    def _post_chunk(self, hold_jid):
        qopt = self._qopt('post', hold_jid)
        cmd = '{}/post_{}_chunk.sh {} {} {}'.format(
            self.script_dir, self.caller_name,
            self.refidx, self.chunk_size, self.call_outname)
        return self.q.submit(qopt, cmd)

    def _post(self, hold_jid):
        if self.chunk_on:
            return self._post_chunk(hold_jid)
        else:
            qopt = self._qopt('post', hold_jid)
            cmd = '{}/post_{}.sh {}'.format(
                self.script_dir, self.caller_name, self.call_outname)
            return self.q.submit(qopt, cmd)
            
    def _coord(self, hold_jid):
        qopt = self._qopt('coord', hold_jid)
        cmd = '{}/snv_coord_{}.sh {} {}'.format(
            self.script_dir, self.caller_name, self.call_file, self.coord_file)
        return self.q.submit(qopt, cmd)

    def _af(self, hold_jid):
        qopt = self._qopt('af', hold_jid)
        cmd = '{}/snv_af.sh {} {} {} {} {}'.format(
            self.script_dir, self.ref, self.clone, self.tissue,
            self.coord_file, self.af_file)
        return self.q.submit(qopt, cmd)

    def _skip_msg(self, msg):
        if self.q.__class__.is_1st_print:
            self.q.__class__.is_1st_print = False
        else:
            print('\x1b[2A', end='\r')
        print('\x1b[2K', end='\r')
        print('Skip {:>16} job: {}.{}\n\n'.format(
            msg, self.sample_name, self.caller_name))

    def _run_msg(self, msg):
        print('\x1b[2A', end='\r')
        print('\x1b[2K', end='\r')
        print('Submitted {:>11} job: {}.{}\n\n'.format(
            msg, self.sample_name, self.caller_name))

    def run(self, clone, tissue):
        self.clone = clone
        self.tissue = tissue
        
        make_dir(self.qerr_dir)
        make_dir(self.qout_dir)
        make_dir(self.call_dir)
        
        hold_jid = ''
        if self.call_file_ok:
            self._skip_msg('calling')
        else:
            hold_jid = self._call()
            hold_jid = self._post(hold_jid)
            self._run_msg('calling')
        if self.af_file_ok:
            self._skip_msg('af_calc')
        else:
            hold_jid = self._coord(hold_jid)
            hold_jid = self._af(hold_jid)
            self._run_msg('af_calc')
        self.hold_jid[self.sample_name] = hold_jid
        
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
