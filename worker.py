import os
import shutil
import subprocess
from collections import defaultdict
from job_queue import GridEngineQueue
from utils import (
    make_dir,
    check_dir,
    check_bam_index,
    check_ref_index,
    check_ref_dict,
    check_outfile,
    get_chunk_intervals,
    get_samplename)


class Worker:
    def __init__(self):
        self.sample_name = None
        self.data_dir = None
        self.out_dir = None
        self._prepare_queue()

    def _prepare_queue(self):
        make_dir('q.out')
        make_dir('q.err')
        self.q = GridEngineQueue()
        self.exec_dir = os.path.dirname(os.path.realpath(__file__))

    def _prepare_qdir(self, caller):
        make_dir(self._qout(caller))
        make_dir(self._qerr(caller))

    def _prepare_datadir(self, data_dir):
        check_dir(data_dir)
        self.data_dir = data_dir

    def _prepare_outdir(self, out_dir):
        make_dir(out_dir)
        self.out_dir = out_dir

    def _subname(self, caller):
        return '{}.{}'.format(self.sample_name, caller)

    def _cmdpath(self, cmd):
        return os.path.join(self.exec_dir, 'job_scripts', cmd)

    def _qout(self, caller):
        return 'q.out/{}'.format(self._subname(caller))

    def _qerr(self, caller):
        return 'q.err/{}'.format(self._subname(caller))

class SomaticCall(Worker):
    def __init__(self, ref, out_dir):
        Worker.__init__(self)
        self._prepare_ref(ref)
        self._prepare_outdir(out_dir)
      
    def _prepare_ref(self, ref):
        check_ref_index(ref)
        check_ref_dict(ref)
        self.ref = ref
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)
        
    def _outdir(self, caller):
        return '{}/{}'.format(self.out_dir, self._subname(caller))

    def _outname(self, caller):
        if caller == 'strelka':
            return self._outdir(caller)
        else:
            return '{}/{}'.format(self._outdir(caller), self._subname(caller))
    
    def _jname(self, caller):
        return 'run_{}.{}'.format(caller, self.sample_name)

    def _jname_chunk(self, caller, interval):
        chrom, start, end = interval
        return '{}.{}-{}-{}'.format(self._jname(caller), chrom, start, end)

    def _qopt(self, caller):
        return '-N {} -o {} -e {}'.format(
            self._jname(caller), self._qout(caller), self._qerr(caller))

    def _qopt_chunk(self, caller, interval):
        return '-N {} -o {} -e {}'.format(
            self._jname_chunk(caller, interval), self._qout(caller), self._qerr(caller))

    def _cmd(self, caller):
        return '{} {} {} {} {}'.format(
            self._cmdpath('run_{}.sh'.format(caller)),
            self.ref, self.clone, self.tissue, self._outname(caller))

    def _cmd_chunk(self, caller, interval):
        chrom, start, end = interval
        cmd = self._cmdpath('run_{}_chunk.sh'.format(caller))
        outname = '{}.{}-{}-{}'.format(self._outname(caller), chrom, start, end)
        interval_str = '{}:{}-{}'.format(chrom, start, end)

        return '{} {} {} {} {} {}'.format(
            cmd, self.ref, self.clone, self.tissue, outname, interval_str)
        
    def _submit(self, caller):
        if caller != 'strelka':
            make_dir(self._outdir(caller))
        self._prepare_qdir(caller)

        qopt = self._qopt(caller)
        cmd = self._cmd(caller)
        return self.q.submit(qopt, cmd)

    def _submit_chunks(self, caller):
        make_dir(self._outdir(caller))
        self._prepare_qdir(caller)
        jids = []

        for interval in self.chunk_intervals:
            qopt = self._qopt_chunk(caller, interval) 
            cmd = self._cmd_chunk(caller, interval)
            jids.append(self.q.submit(qopt, cmd))

        return ','.join(jids)

    def run(self, clone, tissue):
        check_bam_index(clone)
        check_bam_index(tissue)
        self.clone = clone
        self.tissue = tissue
        self.sample_name = get_samplename(clone, tissue)

        jids = {}

#        jids['somaticsniper'] = self._submit('somaticsniper')
        jids['strelka'] = self._submit('strelka')
        jids['mutect'] = self._submit_chunks('mutect')
        jids['varscan'] = self._submit_chunks('varscan')
        
        return jids

class PostProcess(Worker):
    def __init__(self, ref, data_dir):
        Worker.__init__(self)
        self._prepare_ref(ref)
        self._prepare_datadir(data_dir)

    def _prepare_ref(self, ref):
        check_ref_index(ref)
        self.refidx = ref + '.fai'
        self.chunk_intervals = get_chunk_intervals(ref + '.fai', 25000000)

    def _datadir(self, caller):
        return '{}/{}.{}'.format(self.data_dir, self.sample_name, caller)        

    def _jname(self, caller):
        return 'post_{}.{}'.format(caller, self.sample_name)

    def _qopt(self, caller, hold_jid=None):
        if hold_jid == None:
            q_opt_str = '-N {} -o {} -e {}'.format(
                self._jname(caller), self._qout(caller), self._qerr(caller))    
        else:
            q_opt_str = '-N {} -o {} -e {} -hold_jid {}'.format(
                self._jname(caller), self._qout(caller), self._qerr(caller), hold_jid)
        return q_opt_str

    def _cmd(self, caller):
        return '{} {} {}'.format(
            self._cmdpath('post_{}.sh'.format(caller)), self._datadir(caller), self.sample_name)

    def _cmd_chunk(self, caller, chunksize):
        return '{} {} {} {} {}'.format(
            self._cmdpath('post_{}_chunk.sh'.format(caller)),
            self.refidx, chunksize, self._datadir(caller), self.sample_name)
        
    def _submit(self, caller, hold_jid=None):
        qopt = self._qopt(caller, hold_jid)
        cmd = self._cmd(caller)
        return self.q.submit(qopt, cmd)     

    def _submit_chunks(self, caller, hold_jid=None):
        qopt = self._qopt(caller, hold_jid) 
        cmd = self._cmd_chunk(caller, 25000000)
        return self.q.submit(qopt, cmd)

    def run(self, clone, tissue, hold_jid):
        self.sample_name = get_samplename(clone, tissue)
        jids = {}

#        jids['somaticsniper'] = self._submit('somaticsniper', hold_jid['somaticsniper'])
        jids['strelka'] = self._submit('strelka', hold_jid['strelka'])
        jids['mutect'] = self._submit_chunks('mutect', hold_jid['mutect'])
        jids['varscan'] = self._submit_chunks('varscan', hold_jid['varscan'])

        return jids

class SNVCoord(Worker):
    def __init__(self, data_dir, out_dir):
        Worker.__init__(self)
        self._prepare_datadir(data_dir)
        self._prepare_outdir(out_dir)
    
    def _datadir(self, caller):
        return '{}/{}.{}'.format(self.data_dir, self.sample_name, caller)

    def _datafile(self, caller):
        if caller == 'mutect':
            call_file = '{}.mutect.keep.txt'.format(self.sample_name)
        elif caller == 'somaticsniper':
            call_file = '{}.somaticsniper.somatic.vcf'.format(self.sample_name)
        elif caller == 'strelka':
            call_file = 'results/passed.somatic.snvs.vcf'
        elif caller == 'varscan':
            call_file = '{}.varscan.snp.Somatic.hc'.format(self.sample_name)
        return '{}/{}'.format(self._datadir(caller), call_file)
    
    def _outfile(self, caller):
        return '{}/{}.{}.snv_coord.txt'.format(self.out_dir, self.sample_name, caller)

    def _jname(self, caller):
        return 'snv_coord_{}.{}'.format(caller, self.sample_name)

    def _qopt(self, caller, hold_jid=None):
        if hold_jid == None:
            q_opt_str = '-N {} -o {} -e {}'.format(
                self._jname(caller), self._qout(caller), self._qerr(caller))
        else:
            q_opt_str = '-N {} -o {} -e {} -hold_jid {}'.format(
                self._jname(caller), self._qout(caller), self._qerr(caller), hold_jid)
        return q_opt_str

    def _cmd(self, caller):
        return '{} {} {}'.format(
            self._cmdpath('snv_coord_{}.sh'.format(caller)), self._datafile(caller), self._outfile(caller))
        
    def _submit(self, caller, hold_jid=None):
        qopt = self._qopt(caller, hold_jid)
        cmd = self._cmd(caller)
        return self.q.submit(qopt, cmd)

    def run(self, clone, tissue, hold_jid=None):
        self.sample_name = get_samplename(clone, tissue)
        jids = {}

#        for caller in ['mutect', 'somaticsniper', 'strelka', 'varscan']:
        for caller in ['mutect', 'strelka', 'varscan']:
            jids[caller] = self._submit(caller, hold_jid[caller])

        return jids

class AlleleFreq(Worker):
    def __init__(self, ref, data_dir):
        Worker.__init__(self)
        self._prepare_ref(ref)
        self._prepare_datadir(data_dir)

    def _prepare_ref(self, ref):
        check_ref_index(ref)
        self.ref = ref
    
    def _datafile(self, caller):
        return '{}/{}.{}.snv_coord.txt'.format(self.data_dir, self.sample_name, caller)

    def _outfile(self, caller):
        return '{}/{}.{}.snv_AF.txt'.format(self.data_dir, self.sample_name, caller)
    
    def _jname(self, caller):
        return 'snv_AF_{}.{}'.format(caller, self.sample_name)

    def _qopt(self, caller, hold_jid=None):
        if hold_jid == None:
            q_opt_str = '-N {} -o {} -e {}'.format(
                self._jname(caller), self._qout(caller), self._qerr(caller))
        else:
            q_opt_str = '-N {} -o {} -e {} -hold_jid {}'.format(
                self._jname(caller), self._qout(caller), self._qerr(caller), hold_jid)
        return q_opt_str
    
    def _cmd(self, caller):
        return '{} {} {} {} {} {}'.format(
            self._cmdpath('snv_af.sh'), self.ref, self.clone, self.tissue, 
            self._datafile(caller), self._outfile(caller))

    def _submit(self, caller, hold_jid=None):
        qopt = self._qopt(caller, hold_jid)
        cmd = self._cmd(caller)
        return self.q.submit(qopt, cmd)

    def run(self, clone, tissue, hold_jid=None):
        self.sample_name = get_samplename(clone, tissue)
        self.clone = clone
        self.tissue = tissue
        jids = []

#        for caller in ['mutect', 'somaticsniper', 'strelka', 'varscan']:
        for caller in ['mutect', 'strelka', 'varscan']:
            jids.append(self._submit(caller, hold_jid[caller]))

        return ','.join(jids)

class SNVConCall(Worker):
    def __init__(self, data_dir, out_dir):
        Worker.__init__(self)
        self._prepare_datadir(data_dir)
        self._prepare_outdir(out_dir)

    def _jname(self):
        return 'snv_con_call.{}'.format(self.sample_name)

    def _qopt(self, hold_jid=None):
        if hold_jid == None:
            q_opt_str = '-N {} -o {} -e {}'.format(
                self._jname(), self._qout('all'), self._qerr('all'))
        else:
            q_opt_str = '-N {} -o {} -e {} -hold_jid {}'.format(
                self._jname(), self._qout('all'), self._qerr('all'), hold_jid)
        return q_opt_str

    def _cmd(self):
        return '{} {} {} {}'.format(
            self._cmdpath('snv_con_call.sh'), self.sample_name, self.data_dir, self.out_dir)

    def _submit(self, hold_jid=None):
        qopt = self._qopt(hold_jid)
        cmd = self._cmd()
        return self.q.submit(qopt, cmd)

    def run(self, clone, tissue, hold_jid=None):
        self.sample_name = get_samplename(clone, tissue)
        return self._submit(hold_jid)

class Sensitivity(Worker):
    def __init__(self, germ_het, var_1kg, var_na12878, out_dir):
        Worker.__init__(self)
        self.germ_het = germ_het
        self.var_1kg = var_1kg
        self.var_na12878 = var_na12878
        self._prepare_outdir(out_dir)

    def _jname(self):
        return 'sensitivity.{}'.format(self.sample_name)

    def _qopt(self, hold_jid=None):
        if hold_jid == None:
            q_opt_str = '-N {} -o {} -e {}'.format(
                self._jname(), self._qout('all'), self._qerr('all'))
        else:
            q_opt_str = '-N {} -o {} -e {} -hold_jid {}'.format(
                self._jname(), self._qout('all'), self._qerr('all'), hold_jid)
        return q_opt_str

    def _cmd(self):
        return '{} {} {} {} {}'.format(
            self.cmdpath('sensitivity.sh'), self.germ_het, self.var_1kg, self.var_na12878, self.out_dir)